#!/bin/sh
set -e

mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Принимаем ключ хоста автоматически
ssh-keyscan -p "${SSH_PORT:-22}" "${SSH_HOST}" >> /root/.ssh/known_hosts 2>/dev/null

echo "Starting SOCKS5 tunnel → ${SSH_USER:-root}@${SSH_HOST}:${SSH_PORT:-22}"

exec ssh \
  -D "0.0.0.0:1080" \
  -N \
  -p "${SSH_PORT:-22}" \
  -o "ServerAliveInterval=30" \
  -o "ServerAliveCountMax=3" \
  -o "ExitOnForwardFailure=yes" \
  -o "StrictHostKeyChecking=no" \
  "${SSH_USER:-root}@${SSH_HOST}"