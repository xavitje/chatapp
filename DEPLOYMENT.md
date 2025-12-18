# Setup instructies voor VPS deployment

## Stap 1: SSL Certificaat installeren (verplicht voor WebSockets!)

```bash
# Installeer certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Genereer SSL certificaat
sudo certbot --nginx -d chat.drissi.store

# Certificaat wordt automatisch vernieuwd
```

## Stap 2: Nginx configuratie updaten

```bash
# Kopieer de nieuwe nginx config
sudo nano /etc/nginx/sites-available/chat.drissi.store

# Plak de inhoud van nginx-config.conf hier

# Activeer de site
sudo ln -sf /etc/nginx/sites-available/chat.drissi.store /etc/nginx/sites-enabled/

# Test nginx configuratie
sudo nginx -t

# Herstart nginx
sudo systemctl restart nginx
```

## Stap 3: Deploy de applicatie

```bash
# Maak deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## Stap 4: Verificatie

```bash
# Check container logs
sudo docker logs -f chatapp

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Test WebSocket connectie
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: chat.drissi.store" https://chat.drissi.store/api/ws/chat/general
```

## Troubleshooting

### Problem: "502 Bad Gateway"
```bash
# Check if container is running
sudo docker ps

# Check container logs
sudo docker logs chatapp

# Restart container
sudo docker restart chatapp
```

### Problem: "WebSocket connection failed"
```bash
# Verify nginx websocket settings
sudo nginx -t

# Check if SSL is properly configured
sudo certbot certificates

# Restart nginx
sudo systemctl restart nginx
```

### Problem: "Connection timeout"
```bash
# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check if app is listening
sudo netstat -tulpn | grep :5000
```

## Belangrijke wijzigingen

1. ✅ **SSL/HTTPS**: WebSockets werken alleen betrouwbaar met wss:// (secure)
2. ✅ **WebSocket timeouts**: Nginx timeouts verhoogd naar 7 dagen
3. ✅ **Buffering uit**: Belangrijk voor real-time WebSocket communicatie
4. ✅ **File upload limiet**: Verhoogd naar 500MB
5. ✅ **Docker volume**: Database persistent opgeslagen

## Na deployment

De app zal nu beschikbaar zijn op:
- **HTTPS**: https://chat.drissi.store (✅ secure, werkt met WebSockets)
- **HTTP**: http://chat.drissi.store (→ redirect naar HTTPS)

WebSocket URL wordt automatisch:
- `wss://chat.drissi.store/api/ws/chat/general` (secure!)
