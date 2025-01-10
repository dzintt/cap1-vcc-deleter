from modules.cap1 import CapitalOneVCCDeleter
from utils.functions import get_cookies
from utils.dataclasses import Cookie

if __name__ == "__main__":
    cookies = [Cookie(**cookie) for cookie in get_cookies()]
    capital_one_vcc_deleter = CapitalOneVCCDeleter(cookies)
    capital_one_vcc_deleter.get_accounts()
    card_name = input("Enter the name of the VCCs to delete or leave blank to delete all VCCs: ")
    if card_name:
        entries = capital_one_vcc_deleter.get_all_vccs(search=card_name)
    else:
        entries = capital_one_vcc_deleter.get_all_vccs()
    exp_date = input("Enter the expiration date of the VCCs to delete or leave blank to delete all VCCs matching the card name (Format: YYYY-MM): ")
    if exp_date:
        capital_one_vcc_deleter.delete_all_vccs(entries=entries, exp_date=exp_date)
    else:
        capital_one_vcc_deleter.delete_all_vccs(entries=entries)
    print(f"Finished deleting VCCs. Press Enter to exit...")
    input()
