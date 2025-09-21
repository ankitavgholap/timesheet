from developer_discovery import DeveloperDiscovery

discovery = DeveloperDiscovery()
devs = discovery.discover_all_developers(scan_network=False)
print(f'Found {len(devs)} developers')
for dev in devs:
    print(f'- {dev["name"]} at {dev["host"]}:{dev["port"]} ({dev["status"]})')