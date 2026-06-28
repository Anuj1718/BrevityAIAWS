# Cloud Deployment & Infrastructure Architecture

This document serves as a detailed, step-by-step technical log of how the Brevity AI backend was deployed to an AWS GPU instance.

---

## 1. Cloud Compute Provisioning (AWS EC2)
A standard CPU takes ~15-20 seconds to run the Hugging Face BART model. To achieve sub-2-second latency, we provisioned an NVIDIA GPU instance.

1. **Requested Service Quota Increase:**
   - Navigated to AWS Service Quotas -> EC2 -> "All G and VT Spot Instance Requests".
   - Requested an increase to 4 vCPUs to unlock the G-Family instances.
2. **Launched EC2 Instance:**
   - **Instance Type:** `g4dn.xlarge` (4 vCPUs, 16 GB RAM, NVIDIA Tesla T4 GPU 16GB VRAM)
   - **Region:** `ap-south-1` (Mumbai)
   - **Storage:** 96 GB General Purpose SSD (gp3)
   - **OS:** Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.0.1 (Ubuntu 20.04)

---

## 2. Server Configuration & Dependency Management
To avoid dependency hell and library conflicts (specifically `transformers` breaking changes), the backend was containerized.

1. **SSH into the instance:**
   ```bash
   ssh -i "brevity-key.pem" ubuntu@<aws-ip-address>
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/Anuj1718/BrevityAIAWS.git
   cd BrevityAIAWS/Backend
   ```

3. **Install Docker and NVIDIA Container Toolkit:**
   *(The Deep Learning AMI comes pre-installed with CUDA 12.1 and Docker, but we ensured the NVIDIA runtime was configured)*
   ```bash
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

4. **Build the Docker Image:**
   ```bash
   sudo docker build -t brevity-backend .
   ```

---

## 3. Persistent Storage Setup
Instead of using AWS S3 (which introduces network latency), we used Docker Managed Volumes bound to the EC2's Elastic Block Store (EBS) to securely persist uploaded PDFs and outputs.

1. **Create the Docker Volume:**
   ```bash
   sudo docker volume create brevity-uploads
   ```

2. **Run the Container with GPU Passthrough and Volume Mounts:**
   ```bash
   sudo docker run -d \
     --name brevity \
     --gpus all \
     -p 8000:8000 \
     -v brevity-uploads:/app/data/uploads \
     brevity-backend
   ```
   *Note: Because we used a managed volume, data is stored at `/var/lib/docker/volumes/brevity-uploads/_data`, which is locked behind root (`sudo`) access, preventing unauthorized users from scraping uploaded PDFs.*

---

## 4. Secure Networking & Reverse Proxy (Cloudflare Tunnel)
**The Problem:** The React frontend is hosted on Vercel (`HTTPS`). The EC2 backend was a raw IP address (`HTTP`). Chrome blocks this due to **Mixed Content Security Policies**.
**The Solution:** Instead of configuring complex Nginx SSL certificates, we deployed a Cloudflare Tunnel.

1. **Install Cloudflared Daemon:**
   ```bash
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb
   ```

2. **Authenticate with Cloudflare:**
   ```bash
   cloudflared tunnel login
   ```

3. **Create and Route the Tunnel:**
   ```bash
   cloudflared tunnel create brevity-backend-tunnel
   cloudflared tunnel route dns brevity-backend-tunnel api.yourdomain.com
   ```

4. **Configure the Tunnel (`~/.cloudflared/config.yml`):**
   ```yaml
   tunnel: <tunnel-id>
   credentials-file: /home/ubuntu/.cloudflared/<tunnel-id>.json
   ingress:
     - hostname: api.yourdomain.com
       service: http://localhost:8000
     - service: http_status:404
   ```

5. **Run the Tunnel as a Background Service:**
   ```bash
   sudo cloudflared service install
   sudo systemctl start cloudflared
   ```
   *Result:* The local Docker container on port 8000 is now securely exposed to the internet via HTTPS, bypassing the Mixed Content block without opening AWS firewall ports.

---

## 5. Handling CORS (Cross-Origin Resource Sharing)
To prevent unauthorized domains from hitting our expensive GPU API, CORS was strictly configured in FastAPI.

1. **Updated `main.py` in the Backend:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://brevity-ai.vercel.app"], # Strictly Vercel Frontend
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## 6. Frontend Deployment (Vercel)
1. Pushed the `/Frontend` directory to GitHub.
2. Imported the project into Vercel.
3. Configured Environment Variables in Vercel Dashboard:
   ```env
   VITE_API_URL=https://api.yourdomain.com
   ```
4. Clicked **Deploy**.

## 7. Firebase Authentication
1. Initialized Firebase in the Google Cloud Console.
2. Enabled **Email/Password** and **Google Sign-in** providers.
3. Created a Firestore Database to log summarization history.
4. **Configured strict Security Rules:**
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /users/{userId} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
     }
   }
   ```
   *Result:* Users can securely authenticate, and they are cryptographically restricted to reading/writing only their own summarization histories.

---
*End of Deployment Log.*
