import random
import string
from datetime import datetime, timedelta
from pymongo import MongoClient
from faker import Faker

fake = Faker()

continents = [
    {"name": "Africa", "code": "AF"},
    {"name": "Antarctica", "code": "AN"},
    {"name": "Asia", "code": "AS"},
    {"name": "Europe", "code": "EU"},
    {"name": "North America", "code": "NA"},
    {"name": "Australia", "code": "AU"},
    {"name": "South America", "code": "SA"}
]

def generate_dummy_record():
    ip_range = fake.ipv4(network=True)
    ip = fake.ipv4()
    port = random.randint(1024, 65535)
    timestamp = fake.date_time_this_year()
    last_updated_time = timestamp + timedelta(minutes=random.randint(1, 60))
    continent = random.choice(continents)

    geoip = {
        'country_iso_code': fake.country_code(),
        'country': fake.country(),
        'location': {
            'accuracy_radius': random.randint(1, 100),
            'latitude': float(fake.latitude()),
            'longitude': float(fake.longitude()),
            'time_zone': fake.timezone()
        },
        'geo_location': {
            'lat': float(fake.latitude()),
            'lon': float(fake.longitude())
        },
        'continent': continent['name'],
        'continent_code': continent['code'],
        'registered_country': fake.country(),
        'registered_country_iso_code': fake.country_code(),
        'city': fake.city(),
        'postal_code': fake.zipcode(),
        'region': fake.state(),
        'region_iso_code': ''.join(random.choices(string.ascii_uppercase, k=3)),
        'autonomous_system_organization': fake.company(),
        'autonomous_system_number': random.randint(1000, 9999)
    }

    return {
        'victim_ip_range': ip_range,
        'victim_ips': [{'key': ip, 'value': random.randint(1, 1000)}],
        'sensor_ip': fake.ipv4(),
        'victim_ports': [{'key': port, 'value': random.randint(1, 1000)}],
        'sensor_port': random.randint(1024, 65535),
        'count': random.randint(1, 1000),
        'raw_data': '<:/>',
        'rdns': fake.domain_name(),
        'attack_type': random.choice(['WSDiscovery', 'DNS', 'NTP', 'SNMP', 'SSDP', 'CharGen']),
        'timestamp': timestamp.isoformat(),
        'last_updated_time': last_updated_time.isoformat(),
        'geoip': geoip
    }

def populate_mongodb(n, db_name='test_db', collection_name='test_collection'):
    # Connect to MongoDB
    client = MongoClient('connection_string')
    db = client[db_name]
    collection = db[collection_name]

    # Generate and insert dummy records
    records = [generate_dummy_record() for _ in range(n)]
    collection.insert_many(records)
    print(f'Inserted {n} records into {db_name}.{collection_name}')

# Example usage
populate_mongodb(40000)
