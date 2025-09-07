# Checker-connection-DNS-mapping
Server connection monitoring
- Resolves a domain name to an IP address.
- Performs a reverse DNS lookup to find the domain name associated with an IP address.
- Checks if the given string is a valid IPv4 or IPv6 address.
- Checks if the given string is a valid domain name.
- Pings the server if no port is provided, or checks if the specific port is open.
- Placeholder function for restoring a connection.
- Monitors the connection to the server on the specified ports and attempts to restore the connection if any ports are down. In stealth mode, scans are randomized.
- Parses a string of ports and ranges (e.g., '443, 80, 3306-3308, 455 - 600, 3212') into a list of ports, handling irregular spacing and ranges.
- Retrieves a full DNS map for a given domain, including A, AAAA, MX, NS, CNAME, and TXT records.
