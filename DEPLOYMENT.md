# Cloud Deployment & Infrastructure Architecture

This document outlines the final production deployment architecture for the AI Summarization Platform.

## 1. Cloud Compute Provisioning (AWS EC2)
- **Instance Type:** `g4dn.xlarge` (AWS G-Family)
- **Region:** `ap-south-1` (Mumbai) for minimum latency.
- **Hardware Specs:** 
  - 4 vCPUs
  - 16 GB DDR4 RAM
  - 1 NVIDIA Tesla T4 GPU (16GB VRAM)
- **Rationale:** Processing a 406M parameter Hugging Face BART model on a standard CPU takes ~15-20 seconds. Offloading tensor operations to the Tesla T4's 2,560 CUDA cores reduced inference time to ~1.5 seconds.

## 2. Containerization Strategy (Docker)
To avoid dependency hell (Python version conflicts, PyTorch CUDA mismatch, and Transformers library breaking changes), the entire FastAPI backend was containerized.
- **Base Image:** `nvidia/cuda:12.1.0-runtime-ubuntu22.04` (Python 3.10)
- **Execution:** `sudo docker run -d --name brevity-backend --gpus all ...`
- **Benefit:** Total isolation. The container bridges directly to the host's physical GPU while locking `transformers < 5.0.0` securely.

## 3. Data Persistence Layer (EBS & Docker Volumes)
Instead of relying on standard folder mounts or S3 (which introduces network latency), data persistence was handled via **Docker Managed Volumes** backed by the EC2's Elastic Block Store (EBS).
- **Security:** Uploaded PDFs and generated summaries are stored in `/var/lib/docker/volumes/brevity-uploads/_data`. This is owned by the root daemon, making user data completely inaccessible to standard SSH users or potential intruders.
- **Garbage Collection:** A Python cleanup script triggers `os.remove()` immediately after OCR text extraction, ensuring strict privacy compliance and saving EBS storage.

## 4. Secure Networking & Reverse Proxy (Cloudflare Tunnel)
- **The Problem:** The React frontend was hosted securely on Vercel (`HTTPS`), but the EC2 backend was an unencrypted IPv4 address (`HTTP`), resulting in severe browser **Mixed Content Blocking**.
- **The Solution:** A `cloudflared` daemon was installed on the EC2 instance. It establishes a secure outbound reverse-proxy tunnel to Cloudflare's Edge Network, instantly providing bank-grade HTTPS SSL encryption without exposing open ports to the public internet.

## 5. User Authentication & Database (Firebase)
- **Authentication:** Dual-layer auth supporting both standard Email/Password and passwordless Google OAuth 2.0.
- **Database:** Firebase Cloud Firestore stores user session logs and summary metadata.
- **Database Firewall:** Strict Firestore Security Rules (`request.auth.uid == userId`) guarantee that users can only read and write data explicitly tied to their cryptographic UID.

---
*Note: Sensitive variables (IP addresses, specific SSH keys, and `.env` configs) have been intentionally omitted from this documentation for security.*
