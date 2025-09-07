# 🌐 DNS Configuration for PetPlantr.com

## Required DNS Records

### **A Records**
```
petplantr.com        A    [Frontend Server IP]
www.petplantr.com    A    [Frontend Server IP]
api.petplantr.com    A    [API Server IP]
```

### **CNAME Records (Alternative)**
```
www.petplantr.com    CNAME    petplantr.com
```

### **Optional CDN**
```
cdn.petplantr.com    CNAME    [CDN Provider Endpoint]
```

---

## **Cloud Provider Examples**

### **Cloudflare DNS**
```bash
# Add A records
curl -X POST "https://api.cloudflare.com/client/v4/zones/[ZONE_ID]/dns_records" \
  -H "Authorization: Bearer [API_TOKEN]" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "petplantr.com",
    "content": "[SERVER_IP]",
    "ttl": 1
  }'

curl -X POST "https://api.cloudflare.com/client/v4/zones/[ZONE_ID]/dns_records" \
  -H "Authorization: Bearer [API_TOKEN]" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "api.petplantr.com",
    "content": "[API_SERVER_IP]",
    "ttl": 1
  }'
```

### **AWS Route 53**
```json
{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "petplantr.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "[SERVER_IP]"
          }
        ]
      }
    },
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.petplantr.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "[API_SERVER_IP]"
          }
        ]
      }
    }
  ]
}
```

### **Google Cloud DNS**
```bash
# Create A records
gcloud dns record-sets transaction start --zone="petplantr-zone"

gcloud dns record-sets transaction add "[SERVER_IP]" \
  --name="petplantr.com." \
  --ttl="300" \
  --type="A" \
  --zone="petplantr-zone"

gcloud dns record-sets transaction add "[API_SERVER_IP]" \
  --name="api.petplantr.com." \
  --ttl="300" \
  --type="A" \
  --zone="petplantr-zone"

gcloud dns record-sets transaction execute --zone="petplantr-zone"
```

---

## **Verification Commands**

### **Check DNS Propagation**
```bash
# Check A records
dig A petplantr.com
dig A api.petplantr.com

# Check from multiple locations
nslookup petplantr.com 8.8.8.8
nslookup api.petplantr.com 8.8.8.8

# Online tools
# https://dnschecker.org/#A/petplantr.com
# https://whatsmydns.net/#A/petplantr.com
```

### **SSL Certificate Validation**
```bash
# Check SSL after DNS propagation
openssl s_client -connect petplantr.com:443 -servername petplantr.com
openssl s_client -connect api.petplantr.com:443 -servername api.petplantr.com

# Online SSL checker
# https://www.ssllabs.com/ssltest/analyze.html?d=petplantr.com
```

---

## **TTL Recommendations**

| Record Type | TTL | Reason |
|-------------|-----|---------|
| A Records | 300 seconds (5 minutes) | Fast updates during initial setup |
| CNAME | 3600 seconds (1 hour) | Standard for aliases |
| MX Records | 3600 seconds (1 hour) | Email delivery |

After deployment is stable, increase TTL to 86400 (24 hours) for better performance.

---

## **Security Considerations**

### **CAA Records (Optional)**
```
petplantr.com        CAA    0 issue "letsencrypt.org"
petplantr.com        CAA    0 issuewild "letsencrypt.org"
```

### **SPF/DMARC (If using email)**
```
petplantr.com        TXT    "v=spf1 -all"
_dmarc.petplantr.com TXT    "v=DMARC1; p=reject; rua=mailto:admin@petplantr.com"
```

---

## **Testing Checklist**

- [ ] DNS records resolve correctly
- [ ] WWW redirect works
- [ ] SSL certificates are valid
- [ ] Both HTTP and HTTPS work
- [ ] API endpoints are accessible
- [ ] Cross-origin requests work
- [ ] CDN (if configured) serves assets

**Ready for production traffic once DNS propagates! 🌐**
