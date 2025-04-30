

python3 ssh_brute.py <IP>

python3 ssh_brute.py <IP> --port 2222

python3 ssh_brute.py <IP> --users users.txt --passwords passlist.txt --threads 10

proxychains python3 ssh_brute.py <IP>.

nmap -p22 --script ssh2-enum-algos <IP>

nmap -p22 --script ssh2-enum-algos 192.168.1.100

Exploit-DB:searchsploit OpenSSH 2024

GitHub: Repos comohakivvi/openssh-cve-2024-6387.