from urllib3.exceptions import HTTPError as BaseHTTPError
import sys
import json
import os
from pathlib import Path


if float(str(sys.version_info[0]) + '.' + str(sys.version_info[1])) < 3.6:
    raise_ex("Please upgrade to Python 3.7 or later", True)

cwd = os.getcwd()


def raise_ex(msg, terminate):
    print(msg)
    if terminate:
        resetIpJson()
        sys.exit(1)


def createDir():
    newpath = r'zone_files'
    if not os.path.exists(newpath):
        os.makedirs(newpath)


def getzones():
    try:
        configFile = "zones.json"
        h = open("zones.json", 'r')
        zoneFilejson = json.load(h)
        h.close()
    except FileNotFoundError:
        raise_ex(configFile + " was not found", True)
    except PermissionError:
        raise_ex("Invalid permissions trying to open " + configFile, True)
    except json.decoder.JSONDecodeError:
        raise_ex(configFile + " is not a valid json file", True)
    return zoneFilejson


def writeFile(filename, string):
    print("writing File:", os.path.basename(filename))
    try:
        f = open(filename, "w")
        f.write(string)
        f.close()
    except FileNotFoundError:
        raise_ex(filename + " was not found", True)
    except PermissionError:
        raise_ex("Invalid permissions trying to open " + filename, True)


def json2Dict(json):
    # Convert passed json to a dict
    outer = 0
    outerConfig = []
    for item in json:
        innerConfig = []
        innerConfig.extend([0, 1, 2, 3])  # Create dict so it is available for use
        for key in item:
            if key == 'zone':
                innerConfig[0] = json[outer][key]
            elif key == 'records':
                innerConfig[1] = json[outer][key]
            elif key == 'soa':
                innerConfig[2] = json[outer][key]
            elif key == 'email':
                innerConfig[3] = json[outer][key]
            else:
                continue
        outerConfig.append(innerConfig)
        outer += 1
    return outerConfig


def createZoneFiles(zoneDict):
    # Loop over records fcreated by json2Dict
    for zone in zoneDict:
        zoneOutput = "$TTL	604800\n"
        zoneOutput += "@	IN	SOA	{}. {}. (\n".format(zone[2], zone[3].replace("@", "."))
        zoneOutput += "\t\t\t22\t; Serial\n"
        zoneOutput += "\t\t\t24h\t; Refresh\n"
        zoneOutput += "\t\t\t1h\t; Retry\n"
        zoneOutput += "\t\t\t1w\t; Expire\n"
        zoneOutput += "\t\t\t3h)\t; Negative Cache TTL\n\n"
        zoneOutput += "; A records\n"
        a_records = {}
        cname_records = {}
        for record in zone[1]:  # Loop over a records in the dict
            if (record['type'] == 'a'):
                a_records[record['name']] = record['pointer']
            elif (record['type'] == 'cname'):
                cname_records[record['name']] = record['pointer']
        for key, value in a_records.items():
            zoneOutput += "{}\t\t\tIN  A   {}\n".format(key, value)
        zoneOutput += "\n; CNAME records\n"
        for key, value in cname_records.items():
            if (value == '@'):
                value = zone[0]
            zoneOutput += "{}\t\t\tIN  CNAME   {}\n".format(key, value)
        zoneOutput += ";\n"
        file_path = os.path.join(cwd, "zone_files/db."+zone[0])
        writeFile(file_path, zoneOutput)


def createConfLocal(zoneDict):
    # Create named.config.local file with basic information.
    # This could be added on in the future to set slave master options for each domain
    confLocal = ""
    for zone in zoneDict:
        confLocal += "zone \"{}\" ".format(zone[0])
        confLocal += "{\n"
        confLocal += "\ttype master;\n"
        confLocal += "\tfile \"/etc/bind/zones/db.{}\"; # zone file path\n".format(zone[0])
        confLocal += "\tallow-update { none; };\n"
        confLocal += "\tallow-transfer  { 10.0.0.33; 10.0.0.37; };\n"
        confLocal += "\talso-notify { 10.0.0.33; 10.0.0.37; };\n"
        confLocal += "};\n\n"
    file_path = os.path.join(cwd, "named.conf.local")
    writeFile(file_path, confLocal)


def main():
    createDir()
    zoneFilejson = getzones()
    zoneDict = json2Dict(zoneFilejson)
    createConfLocal(zoneDict)
    createZoneFiles(zoneDict)


main()
