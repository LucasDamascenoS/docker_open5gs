import argparse
from pymongo import MongoClient

def main():
    parser = argparse.ArgumentParser(description="Insert Open5GS subscribers into MongoDB")
    parser.add_argument("--count", type=int, required=True, help="Number of subscribers to insert")
    parser.add_argument("--start", type=str, required=True, help="Starting IMSI (included)")
    args = parser.parse_args()

    start_imsi = args.start.zfill(len(args.start))
    num_entries = args.count

    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['open5gs']
    collection = db['subscribers']

    current_imsi = start_imsi  # include starting IMSI

    for i in range(num_entries):
        base_data = {
            'ambr': {
                'downlink': {'value': 1, 'unit': 3},
                'uplink': {'value': 1, 'unit': 3}
            },
            'schema_version': 1,
            'msisdn': [],
            'imeisv': [],
            'mme_host': [],
            'mme_realm': [],
            'purge_flag': [],
            'access_restriction_data': 32,
            'subscriber_status': 0,
            'network_access_mode': 0,
            'subscribed_rau_tau_timer': 12,
            'imsi': current_imsi,
            'security': {
                'k': '00112233445566778899AABBCCDDEEFF',
                'amf': '8000',
                'op': None,
                'opc': '00112233445566778899AABBCCDDEEFF'
            },
            'slice': [{
                'sst': 1,
                'sd': '000001',
                'default_indicator': True,
                'session': [{
                    'qos': {
                        'arp': {
                            'priority_level': 8,
                            'pre_emption_capability': 1,
                            'pre_emption_vulnerability': 1
                        },
                        'index': 9
                    },
                    'ambr': {
                        'downlink': {'value': 1, 'unit': 3},
                        'uplink': {'value': 1, 'unit': 3}
                    },
                    '_id': 1,
                    'name': 'internet',
                    'type': 3,
                    'pcc_rule': []
                }]
            }],
            '__v': 0
        }

        collection.insert_one(base_data)
        #print(f"Inserted IMSI: {current_imsi}")

        # Prepare next IMSI
        current_imsi = str(int(current_imsi) + 1).zfill(len(args.start))

    print(f"\nSuccessfully inserted {num_entries} subscribers starting from IMSI {start_imsi}")

if __name__ == "__main__":
    main()