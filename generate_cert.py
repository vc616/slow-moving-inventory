from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime
import os
import ipaddress

base_dir = os.path.dirname(os.path.abspath(__file__))
ssl_dir = os.path.join(base_dir, "ssl")
os.makedirs(ssl_dir, exist_ok=True)

key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Shanghai"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Shanghai"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "InventorySystem"),
    x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    datetime.datetime.utcnow() + datetime.timedelta(days=365)
).add_extension(
    x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address('127.0.0.1'))
    ]),
    critical=False,
).sign(key, hashes.SHA256(), default_backend())

key_path = os.path.join(ssl_dir, "key.pem")
with open(key_path, "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

cert_path = os.path.join(ssl_dir, "cert.pem")
with open(cert_path, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print(f"Certificate: {cert_path}")
print(f"Key: {key_path}")
