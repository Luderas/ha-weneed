"""API client for WeNeed / Firebase Firestore."""

from datetime import datetime, timedelta, timezone
import logging
import uuid
import requests

from .const import FIREBASE_API_KEY, PROJECT_ID

_LOGGER = logging.getLogger(__name__)


class WeNeedApi:
    """Client to interact with WeNeed Firebase Firestore backend."""

    def __init__(self, email: str, password: str, list_id: str | None = None):
        self._email = email
        self._password = password
        self._list_id = list_id
        self._id_token = None
        self._token_expiry = datetime.min.replace(tzinfo=timezone.utc)
        self._user_id = None
        # Persistent session to reuse TCP/TLS connections
        self._session = requests.Session()

    @property
    def list_id(self) -> str | None:
        """Return the current shopping list ID."""
        return self._list_id

    @list_id.setter
    def list_id(self, value: str) -> None:
        """Set the current shopping list ID."""
        self._list_id = value

    def authenticate(self) -> str:
        """Authenticate with Firebase Auth or reuse cached token."""
        now = datetime.now(timezone.utc)
        if self._id_token and now < self._token_expiry:
            return self._id_token

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        payload = {
            "email": self._email,
            "password": self._password,
            "returnSecureToken": True,
        }
        res = self._session.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            raise ValueError(f"Authentication failed: {res.text}")

        data = res.json()
        self._id_token = data["idToken"]
        self._user_id = data.get("localId", "user")
        self._token_expiry = now + timedelta(seconds=int(data.get("expiresIn", 3600)) - 60)
        return self._id_token

    def get_shopping_lists(self) -> list[dict]:
        """Fetch all shopping lists belonging to or shared with the user."""
        token = self.authenticate()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:runQuery"

        lists = {}

        query_owner = {
            "structuredQuery": {
                "from": [{"collectionId": "v2_shoppingLists"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "data.owner"},
                        "op": "EQUAL",
                        "value": {"stringValue": self._user_id},
                    }
                },
            }
        }
        query_participant = {
            "structuredQuery": {
                "from": [{"collectionId": "v2_shoppingLists"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "data.participants"},
                        "op": "ARRAY_CONTAINS",
                        "value": {"stringValue": self._user_id},
                    }
                },
            }
        }

        for q in [query_owner, query_participant]:
            try:
                res = self._session.post(url, headers=headers, json=q, timeout=10)
                if res.status_code == 200:
                    for row in res.json():
                        doc = row.get("document")
                        if not doc:
                            continue
                        doc_id = doc["name"].split("/")[-1]
                        fields = doc.get("fields", {})
                        data_map = fields.get("data", {}).get("mapValue", {}).get("fields", {})
                        list_name = data_map.get("name", {}).get("stringValue", "Einkaufsliste")
                        item_count = int(
                            data_map.get("numberOfUncheckedProducts", {}).get("integerValue", 0)
                        )
                        lists[doc_id] = {
                            "id": doc_id,
                            "name": list_name,
                            "item_count": item_count,
                        }
            except Exception as e:
                _LOGGER.debug("Querying shopping lists returned: %s", e)

        return list(lists.values())

    def get_items(self) -> list[dict]:
        """Fetch all items from the current shopping list."""
        if not self._list_id:
            raise ValueError("No shopping list ID configured")

        token = self.authenticate()
        headers = {"Authorization": f"Bearer {token}"}
        url = (
            f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/"
            f"documents/v2_shoppingLists/{self._list_id}/v2_shoppingListProducts?pageSize=300"
        )
        res = self._session.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        docs = res.json().get("documents", [])
        items = []

        for doc in docs:
            doc_id = doc["name"].split("/")[-1]
            fields = doc.get("fields", {})
            data_map = fields.get("data", {}).get("mapValue", {}).get("fields", {})

            name_fields = data_map.get("name", {}).get("mapValue", {}).get("fields", {})
            item_name = (
                name_fields.get("de", {}).get("stringValue")
                or name_fields.get("en", {}).get("stringValue")
                or name_fields.get("fr", {}).get("stringValue")
                or name_fields.get("it", {}).get("stringValue")
                or "Artikel"
            )

            is_checked = data_map.get("checked", {}).get("booleanValue", False)

            items.append({
                "uid": doc_id,
                "name": item_name,
                "checked": is_checked,
            })

        return items

    def add_item(self, summary: str) -> str:
        """Add a new item to the shopping list and return the generated ID."""
        if not self._list_id:
            raise ValueError("No shopping list ID configured")

        token = self.authenticate()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        item_id = str(uuid.uuid4()).upper()
        now_iso = (
            datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

        body = {
            "fields": {
                "origin": {
                    "mapValue": {
                        "fields": {
                            "createdAt": {"timestampValue": now_iso},
                            "createdBy": {"stringValue": self._user_id},
                            "source": {
                                "mapValue": {
                                    "fields": {
                                        "originator": {"stringValue": "homeassistant"},
                                        "platform": {"stringValue": "api"},
                                        "appVersion": {"stringValue": "1.0.0"},
                                        "meta": {"stringValue": ""},
                                    }
                                }
                            },
                        }
                    }
                },
                "activity": {
                    "mapValue": {
                        "fields": {
                            "lastModifiedAt": {"timestampValue": now_iso},
                            "lastModifiedBy": {"stringValue": self._user_id},
                            "source": {
                                "mapValue": {
                                    "fields": {
                                        "originator": {"stringValue": "homeassistant"},
                                        "platform": {"stringValue": "api"},
                                        "appVersion": {"stringValue": "1.0.0"},
                                        "meta": {"stringValue": ""},
                                    }
                                }
                            },
                        }
                    }
                },
                "data": {
                    "mapValue": {
                        "fields": {
                            "name": {
                                "mapValue": {
                                    "fields": {
                                        "de": {"stringValue": summary},
                                        "en": {"stringValue": summary},
                                        "fr": {"stringValue": summary},
                                        "it": {"stringValue": summary},
                                    }
                                }
                            },
                            "checked": {"booleanValue": False},
                            "status": {"stringValue": "active"},
                            "source": {"stringValue": "user"},
                            "type": {"stringValue": "OTHER"},
                            "shoppingListId": {"stringValue": self._list_id},
                            "brands": {"stringValue": ""},
                            "imageName": {"stringValue": ""},
                            "description": {"stringValue": ""},
                            "popularityIndex": {"integerValue": "0"},
                            "lastCheckedAt": {"nullValue": None},
                            "coopProduct": {"nullValue": None},
                            "attachmentImage": {"nullValue": None},
                        }
                    }
                },
            }
        }

        url = (
            f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/"
            f"documents/v2_shoppingLists/{self._list_id}/v2_shoppingListProducts?documentId={item_id}"
        )
        res = self._session.post(url, headers=headers, json=body, timeout=10)
        res.raise_for_status()
        return item_id

    def update_item_status(self, uid: str, checked: bool) -> None:
        """Mark an item as checked or unchecked."""
        if not self._list_id:
            raise ValueError("No shopping list ID configured")

        token = self.authenticate()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "fields": {
                "data": {
                    "mapValue": {
                        "fields": {
                            "checked": {"booleanValue": checked}
                        }
                    }
                }
            }
        }
        url = (
            f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/"
            f"documents/v2_shoppingLists/{self._list_id}/v2_shoppingListProducts/{uid}?updateMask.fieldPaths=data.checked"
        )
        res = self._session.patch(url, headers=headers, json=body, timeout=10)
        res.raise_for_status()

    def delete_item(self, uid: str) -> None:
        """Delete an item from WeNeed."""
        if not self._list_id:
            raise ValueError("No shopping list ID configured")

        token = self.authenticate()
        headers = {"Authorization": f"Bearer {token}"}
        url = (
            f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/"
            f"documents/v2_shoppingLists/{self._list_id}/v2_shoppingListProducts/{uid}"
        )
        res = self._session.delete(url, headers=headers, timeout=10)
        res.raise_for_status()
