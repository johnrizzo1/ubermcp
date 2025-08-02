#!/bin/bash
# Generate self-signed SSL certificates for HTTPS

# Create certs directory
mkdir -p certs

# Generate private key
openssl genrsa -out certs/server.key 2048

# Generate certificate signing request
openssl req -new -key certs/server.key -out certs/server.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in certs/server.csr -signkey certs/server.key -out certs/server.crt

# Clean up CSR
rm certs/server.csr

echo "SSL certificates generated in certs/ directory"
echo "- certs/server.key (private key)"
echo "- certs/server.crt (certificate)"