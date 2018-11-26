from os.path import isfile, expanduser
import ndex2
import json
nicecx = ndex2.NiceCXNetwork
Ndex2 = ndex2.Ndex2



example_config = {
    "connections" : {
        "main" : {
            "server" : "http://dev.ndexbio.org",
            "username" : "my_user",
            "password" : "my_pass"
        }
    }
}

def load_tutorial_config(connection_name):
    username = None
    password = None
    config_file = expanduser("~/ndex_tutorial_config.json")
    server = "http://public.ndexbio.org"

    if isfile(config_file):
        file = open(config_file, "r")
        config = json.load(file)
        file.close()
        connections = config.get("connections")
        if connections:
            if connection_name:
                connection = connections.get(connection_name)
                if connection and connection.get("password") and config.get("username"):
                    if connection.get("server"):
                        server = connection.get("server")
                    username = connection.get("username")
                    password = connection.get("password")
            else:
                print("Error: " + str(connection_name) + " does not define both username and password")
        else:
            print("Error: " + config_file + " does not define any connections")
    else:
        print("Error: " + config_file + " was not found")

    return server, username, password
