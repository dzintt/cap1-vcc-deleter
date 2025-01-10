import requests
import concurrent.futures
from utils.dataclasses import Cookie, VCCEntry

class CapitalOneVCCDeleter:
    def __init__(self, cookies: list[Cookie]):
        self.card_ids = []
        self.session = requests.Session()
        for cookie in cookies:
            self.session.cookies.set(cookie.name, cookie.value)
        self.session.headers = {
            "accept": "application/json;v=2",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

    def _fetch_single_page(self, card_reference_id: str, offset: int, limit: int, payload: dict) -> list[VCCEntry]:
        page_url = f"https://myaccounts.capitalone.com/web-api/private/25419/commerce-virtual-numbers?limit={limit}&offset={offset}"
        print(f"Fetching VCCs for {card_reference_id} (offset: {offset})")
        
        while True:
            response = self.session.post(page_url, json=payload)
            if "id" in response.json() and response.json()["id"] == "800000":
                print(f"Retrying offset {offset} due to error: {response.text.strip()}")
                continue
            return [VCCEntry(**entry) for entry in response.json()["entries"]]

    def _fetch_card_vccs(self, card_reference_id: str, search: str = None) -> list[VCCEntry]:
        limit = 50
        url = f"https://myaccounts.capitalone.com/web-api/private/25419/commerce-virtual-numbers?limit={limit}&offset=0"
        payload = {
            "referenceId": card_reference_id,
            "referenceIdType": "ACCOUNT",
            "tokenStatus": ["ACTIVE"],
            "filterCriteria": [],
            "sortCriteria": []
        }
        if search:
            payload["filterCriteria"].append({"field": "TOKEN_NAME", "value": search, "operator": "LIKE"})

        self.session.headers["accept"] = "application/json;v=2"

        while True:
            response = self.session.post(url, json=payload)
            if "id" in response.json() and response.json()["id"] == "800000":
                print(f"Retrying initial request due to error: {response.text.strip()}")
                continue
            break

        total_count = response.json()["count"]
        max_offset = (total_count + limit - 1) // limit 
        all_entries = [VCCEntry(**entry) for entry in response.json()["entries"]]

        if max_offset > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                future_to_offset = {
                    executor.submit(self._fetch_single_page, card_reference_id, offset, limit, payload): offset 
                    for offset in range(1, max_offset)
                }
                
                for future in concurrent.futures.as_completed(future_to_offset):
                    offset = future_to_offset[future]
                    try:
                        entries = future.result()
                        all_entries.extend(entries)
                        print(f"Found {len(all_entries)}/{total_count} entries for {card_reference_id}")
                    except Exception as e:
                        print(f"Error fetching offset {offset}: {str(e)}")

        print(f"Finished fetching VCCs for {card_reference_id}. Found {len(all_entries)}/{total_count} entries")
        return all_entries
    
    def get_accounts(self):
        self.session.headers["accept"] = "application/json;v=1"
        response = self.session.get("https://myaccounts.capitalone.com/web-api/private/1491939/edge/customer/profile/preferences")
        result = response.json()
        print("Found", len(result["accountDisplayOrder"]), "cards")
        self.card_ids = result["accountDisplayOrder"]

    def get_all_vccs(self, search: str = None) -> list[VCCEntry]:
        entries = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_card = {
                executor.submit(self._fetch_card_vccs, card_id, search): card_id 
                for card_id in self.card_ids
            }
            for future in concurrent.futures.as_completed(future_to_card):
                entries.extend(future.result())

        print("Found", len(entries), "VCCs across all accounts")
        return entries
    
    def delete_all_vccs(self, entries: list[VCCEntry], exp_date: str = None) -> None:
        print("Deleting", len(entries), "VCCs")

        if exp_date:
            matching_entries = [entry for entry in entries if entry.formatted_token_expiration_date == exp_date]
        else:
            matching_entries = entries

        total = len(matching_entries)
        print(f"Found {total} entries matching criteria")

        if exp_date:
            print(f"Expiration date filter: {exp_date}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_to_entry = {
                executor.submit(self.delete_vcc, entry): entry 
                for entry in matching_entries
            }
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_entry)):
                entry = future_to_entry[future]
                print(f"Deleting {entry.token_name} (*****{entry.token_last_four}) ({i+1}/{total})")
                future.result()

    def delete_vcc(self, entry: VCCEntry) -> None:
        sent_req = False
        while not sent_req:
            payload = {
                "cardReferenceId": entry.card_reference_id,
                "cardName": "",
                "cardLastFour": "",
                "tokenReferenceId": entry.token_reference_id,
                "isDeleted": True,
            "allowAuthorizations": True,
            "tokenName": entry.token_name,
                "tokenLastFour": entry.token_last_four,
            }
            self.session.headers["accept"] = "application/json;v=2"
            delete_response = self.session.put("https://myaccounts.capitalone.com/web-api/private/25419/commerce-virtual-numbers", json=payload)
            print(f"Status: {delete_response.text.strip()}")
            if "id" in delete_response.json() and delete_response.json()["id"] == "800000":
                print(f"Retrying due to error: {delete_response.text.strip()}")
                continue
            if "cloudfront" in delete_response.text.strip():
                print(f"Retrying due to cloudfront error")
                continue
            if "Capital One Sign In" in delete_response.text.strip():
                raise Exception("Account was signed out. Cookies likely expired. Please add new cookies and try again.")
            sent_req = True

