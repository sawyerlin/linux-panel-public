iptables -F
iptables -A OUTPUT -p tcp --sport 80 --tcp-flags SYN,RST,ACK,FIN,PSH SYN,ACK -j NFQUEUE --queue-num 668
iptables -A OUTPUT -p tcp --sport 443 --tcp-flags SYN,RST,ACK,FIN,PSH SYN,ACK -j NFQUEUE --queue-num 669

cp /www/server/mdserver-web/geneva/geneva_http* /usr/lib/systemd/system/
systemctl enable geneva_http.service
systemctl enable geneva_https.service