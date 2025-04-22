import google.auth
from google.cloud import dns
import yaml

def update_dns_records(projects, dns_records, zone):
    """
    Updates DNS records in the specified Google Cloud projects.

    Args:
        projects (list): List of Google Cloud project IDs.
        dns_records (list): List of DNS records to add. Each record should be a dictionary with keys:
            - 'name': The DNS record name.
            - 'type': The DNS record type (e.g., 'A', 'CNAME').
            - 'ttl': The time-to-live for the record.
            - 'rrdatas': A list of resource record data.
        zone (str): The managed zone name.
    """
    for project in projects:
        print(f"Processing project: {project}")
        try:
            client = dns.Client(project=project)

            zone_obj = client.zone(zone)

            if not zone_obj.exists():
                print(f"Zone {zone} does not exist in project {project}.")
                continue

            changes = zone_obj.changes()
            existing_records = list(zone_obj.list_resource_record_sets())

            for record in dns_records:
                # Check if the record already exists
                record_exists = any(
                    r.name == record['name'] and r.record_type == record['type'] for r in existing_records
                )

                if record_exists:
                    print(f"Record {record['name']} already exists in zone {zone}.")
                else:
                    try:
                        # Add the record if it doesn't exist
                        new_record = zone_obj.resource_record_set(
                            record['name'], record['type'], record['ttl'], record['rrdatas']
                        )
                        changes.add_record_set(new_record)
                        changes.create()
                        print(f"Added record {record['name']} to zone {zone}.")
                    except google.api_core.exceptions.Conflict as conflict_error:
                        print(f"Conflict error: {conflict_error}. Skipping record {record['name']}.")

        except Exception as e:
            print(f"Error processing project {project}: {e}")

def load_config_from_yaml(file_path):
    """
    Loads configuration from a YAML file.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        tuple: A tuple containing the list of projects, DNS records, and the zone.
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        return config.get('projects', []), config.get('dns_records', []), config.get('zone', None)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python update_dns_records.py <config_file.yaml>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        projects, dns_records, zone = load_config_from_yaml(config_file)
        if not zone:
            raise ValueError("Zone must be specified in the configuration file.")
        update_dns_records(projects, dns_records, zone)
    except Exception as e:
        print(f"Error loading configuration: {e}")