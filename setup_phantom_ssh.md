# Setting Up SSH Access to Phantom Laptop

**Date:** October 18, 2025
**Target:** phantom-ops (100.72.142.62)
**User:** aaliy
**Purpose:** Copy instrumentation PDF for CRM agent training

---

## Issue

Cannot SSH into phantom laptop with user `aaliy`. Authentication is failing with:
```
Permission denied (publickey,password)
```

---

## Solutions

### Option 1: Add SSH Key to Phantom Laptop (Recommended)

**On iac1 (this server), generate a key for aaliy if not exists:**
```bash
# Check if we have a key for aaliy
ls -la ~/.ssh/id_phantom_ops*

# The key exists: ~/.ssh/id_phantom_ops
# Public key: ~/.ssh/id_phantom_ops.pub
```

**Copy public key to phantom laptop:**

You'll need to physically access the phantom laptop or have someone with access run:

```bash
# On phantom laptop, as user aaliy:
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add iac1's public key to authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHpQZ5f... wil@iac1" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

**Get our public key:**
```bash
cat ~/.ssh/id_phantom_ops.pub
```

### Option 2: Use Tailscale File Transfer (Easier)

Tailscale supports file transfer without SSH:

```bash
# Send file from phantom to iac1 (run on phantom laptop):
tailscale file cp /home/aaliy/Downloads/instrumentacion-industrial-antonio-creus.pdf iac1:

# Or receive file on iac1 (this server):
tailscale file get /home/aaliy/Downloads/instrumentacion-industrial-antonio-creus.pdf
```

### Option 3: Alternative - Use SCP with Password (If Password Auth Enabled)

```bash
# This requires aaliy's password
scp aaliy@100.72.142.62:/home/aaliy/Downloads/instrumentacion-industrial-antonio-creus.pdf ~/
```

### Option 4: Ask User to Copy Via Shared Folder

If phantom laptop has a shared folder or cloud sync:
- Ask aaliy to copy the PDF to a shared location
- Download from there to iac1

---

## SSH Authentication Results (Oct 18, 2025 - 01:45 UTC)

**Password Provided:** 1234
**Result:** ❌ Authentication failed

**Tests Performed:**
1. Standard SSH with password: TIMEOUT (connection hangs)
2. Tailscale SSH: Permission denied (publickey,password)
3. Port 22 connectivity: ✅ Port is open and accessible
4. Tailscale status: ✅ Direct connection active

**Conclusion:** Password authentication appears to be disabled on phantom-ops SSH daemon, or the password is incorrect for SSH access.

---

## ✅ RECOMMENDED SOLUTION: Tailscale File Transfer (No SSH Required!)

**On phantom-ops laptop** (user aaliy should run):

### Method 1: Use the Helper Script
```bash
# Copy and run the helper script on phantom laptop
bash send_pdf_from_phantom.sh
```

### Method 2: Manual Tailscale File Send
```bash
# Send file from phantom to iac1
tailscale file cp /home/aaliy/Downloads/instrumentacion-industrial-antonio-creus.pdf iac1:

# Verify it was sent
tailscale status
```

**On iac1** (run after file is sent):
```bash
# Receive the file
tailscale file get ~/

# Verify it arrived
ls -lh ~/instrumentacion-industrial-antonio-creus.pdf
```

---

## Alternative Options (If Tailscale File Transfer Not Working)

**Option 1: Enable SSH Password Authentication on Phantom**
```bash
# On phantom laptop, edit SSH config:
sudo nano /etc/ssh/sshd_config

# Add or change:
PasswordAuthentication yes

# Restart SSH:
sudo systemctl restart sshd
```

**Option 2: Copy Public Key to Phantom**
```bash
# On iac1, display public key:
cat ~/.ssh/id_phantom_ops.pub

# On phantom laptop as aaliy:
mkdir -p ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

**Option 3: Email or Cloud Transfer**
- User emails PDF to w.aroca@insaing.com
- Or uploads to Google Drive/Dropbox and shares link

---

## Recommended Next Steps

**EASIEST SOLUTION** (no SSH setup required):
1. ✅ User runs the helper script on phantom laptop: `bash send_pdf_from_phantom.sh`
2. ✅ Or user manually runs: `tailscale file cp /home/aaliy/Downloads/instrumentacion-industrial-antonio-creus.pdf iac1:`
3. ✅ On iac1, receive file: `tailscale file get ~/`
4. ✅ Verify and process the PDF for CRM agents

---

## File Information

**Source File:** `/home/aaliy/Downloads/instrumentacion-industrial-antonio-creus.pdf`
**Target Location:** `/home/wil/` on iac1
**Purpose:** Industrial instrumentation reference for CRM AI agents
**Use Case:** Training agents on industrial automation equipment and standards

---

## Once File is Retrieved

After getting the PDF, we'll need to:

1. **Extract text content:**
```bash
sudo apt-get install -y poppler-utils
pdftotext instrumentacion-industrial-antonio-creus.pdf instrumentation.txt
```

2. **Index for AI agents:**
- Create knowledge base in PostgreSQL
- Or use Qdrant vector database (Phase 5)
- Or simply make it available to agents for RAG

3. **Use cases for CRM agents:**
- Equipment recommendation agent (learn component specs)
- Quote generation agent (understand instrumentation)
- P&ID generation agent (industrial symbols and standards)
- Technical proposal agent (reference material)

---

## 📦 Helper Script Created

**Location:** `/home/wil/send_pdf_from_phantom.sh`
**Purpose:** Run on phantom laptop to easily send PDF via Tailscale
**Size:** 1.5 KB
**Status:** Ready to use

**To share with phantom laptop:**
1. Copy script content from iac1
2. Or email the script to aaliy
3. Or user manually runs the tailscale file cp command

---

**Status:** ⏸️ BLOCKED - SSH password authentication disabled on phantom-ops
**Next Action:** User should run Tailscale file transfer on phantom laptop (easiest solution)
**Alternative:** Enable SSH password auth or add public key to phantom laptop
**Updated:** October 18, 2025 01:45 UTC
