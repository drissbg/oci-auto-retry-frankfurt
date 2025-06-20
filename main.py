import oci
import os
import time
import smtplib
from email.mime.text import MIMEText
from oci.signer import Signer

# Use in-memory signer with private key string from environment
signer = Signer(
    tenancy=os.getenv("OCI_TENANCY_ID"),
    user=os.getenv("OCI_USER_ID"),
    fingerprint=os.getenv("OCI_KEY_FINGERPRINT"),
    private_key=os.getenv("OCI_API_KEY")
)

config = {
    "region": os.getenv("OCI_REGION")
}

subnet_id = os.getenv("OCI_SUBNET_ID")
image_id = os.getenv("OCI_IMAGE_ID")
ssh_key = os.getenv("OCI_SSH_PUBLIC_KEY")
shape = os.getenv("OCI_SHAPE")
ocpus = int(os.getenv("OCI_OCPUS", "1"))
memory = int(os.getenv("OCI_MEMORY_IN_GBS", "6"))
ads = os.getenv("OCI_AVAILABILITY_DOMAINS", "").split(",")
sleep_seconds = int(os.getenv("SLEEP_SECONDS", 60))

# Email settings
email_host = os.getenv("EMAIL_HOST")
email_port = int(os.getenv("EMAIL_PORT", "587"))
email_user = os.getenv("EMAIL_USERNAME")
email_pass = os.getenv("EMAIL_PASSWORD")
email_to   = os.getenv("EMAIL_TO")

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_user
    msg["To"] = email_to
    try:
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
        print("[EMAIL SENT]")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

def attempt_instance(ad, compute):
    try:
        print(f"[TRYING] {ad}")
        launch_details = oci.core.models.LaunchInstanceDetails(
            availability_domain=ad.strip(),
            compartment_id=os.getenv("OCI_TENANCY_ID"),
            shape=shape,
            source_details=oci.core.models.InstanceSourceViaImageDetails(
                source_type="image",
                image_id=image_id,
                boot_volume_size_in_gbs=50
            ),
            create_vnic_details=oci.core.models.CreateVnicDetails(
                subnet_id=subnet_id,
                assign_public_ip=True
            ),
            metadata={"ssh_authorized_keys": ssh_key},
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=ocpus,
                memory_in_gbs=memory
            ),
            display_name="oci-arm-auto"
        )
        response = compute.launch_instance(launch_details)
        print(f"[SUCCESS] Instance launched in {ad}")
        send_email("OCI Instance Created", f"Instance created in {ad}\nOCID: {response.data.id}")
        return True
    except oci.exceptions.ServiceError as e:
        if "Out of host capacity" in str(e.message):
            print(f"[RETRY] Capacity error in {ad}")
        else:
            print(f"[FAILURE] {ad} → {e.message}")
        return False

def main():
    compute = oci.core.ComputeClient(config, signer=signer)
    while True:
        for ad in ads:
            if attempt_instance(ad, compute):
                return
        print(f"[WAITING] Sleeping {sleep_seconds} seconds...")
        time.sleep(sleep_seconds)

if __name__ == "__main__":
    main()
