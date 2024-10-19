from os import environ

secrets = {}

try:
  with open(".env", "r") as f:
    values = f.readlines()
    for value in values:
      line = value.rstrip().split("=", 1)
      secrets[line[0]] = line[1]
except Exception as e:
  print(e)
  exit()