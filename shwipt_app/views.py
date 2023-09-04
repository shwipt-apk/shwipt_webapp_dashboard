# from firebase_admin import credentials, initialize_app

# creds = credentials.Certificate({
#   "type": "service_account",
#   "project_id": "shwipt-dev",
#   "private_key_id": "e1804c0a7887e503fb4a374d8c01f67c3131cfc0",
#   "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCp1W3QBaPzMEuq\nXWivQrf2ma4daZ/jurdAU56kEKDx7BvCz5ro0txR7DGHo1NEPO5FnvOvvcMtZ1AM\nz4/r2hP8XcrKdFiwsVI8DBA3G0SmV22zT/xq+KlpYqvUzWbN/kYV6imPK/9fHeuz\nOb5Mp+mf7XAvOlkGKpWj0nVEtnPC5QeSr1axJshlNAAoh0da/4qCexZCfgnhlSvG\nz55M7+2C4gs8NvoAK0q+W9f/2EY9o7C8qQHQ6UQXiT8+o/lyilDCovCbsj+FBsKe\nZzYX8E3kLfg/08RxmkJEQMiqeNJ1wYqaOHTHrsPu8W2QLIGsubYIwUrVp868+eC8\nXktLm9cDAgMBAAECggEACzjdpTnCMB8YWN0MPkx30HUuMqZYmNktI7SCzo+Euweh\ne/lw4IKSaV1klnRd26v1CKesrYep/nWNrhMHDQwfdvURodgXRjGpX+tiJOoJ2r37\nMzaNVNoyg5KwDQM3kFQFeIw9C8dZ/ASDnxepMfKEdvtfBtfhqw0kTytocU5nDtEs\n3zFvLwlL59qkGuIE4oHAHxZOH5J3i8Lj6GS2Hg4I20vb8ejioNlai6hUsPlSbmnB\nlbYXZ7ayafYBBfXq+79ailh5glgVpC+/D8AKVA4f/7eoQR+Z3UMEb3JHKGWVcp+I\n1/jPS9dwOrWJru4lDnWZ/+khgzaXfolZCcHEvwa80QKBgQDZK2TtG8cTcm4/AqLP\ntfwOM+3tAgD22RIfgGUb296XtRa2kXBQAUfZ2fn6Fy/zP7hjxhP8TJWB5xFbmoH3\njK5+hVilUd47YSfAulUGsVDWrx7ncV1I67cRGW0Ugi7LtiNumcajhk21W1jAqqpo\noJEMGVsoXa3fUYdfBwzi0XmjEQKBgQDIM09bGhbo0Dd3OPq89MCl2Fqp+7tYewXF\npQ2UR2HbFwaUb9kL90N7AA5BvKy74OlwSWSCpYO5KjT4qKid7HWunEm9t6E8m+l0\nyEBKaToMuElEQAC5mjrv/piNbST/6I5i+Dftaj5hp57rHheK9QF4/JqD/S/lPode\nvDdlptNw0wKBgA9GsCjFpXFGwV6JTu6RfJN7L6dWVr8GcfHpVDNrefLt+BULkfzu\nuiEm5iCjdOoFd3D9Q/ahZHroyB3Ldoz1Rmj79EpcwecnZGZ4NPbtjiQr2V6qaMdy\nXUREp5mjtqr5uvBSvNhP4DN7o3iaCLanZMyXFAR44nws/fq/QjbKSWYhAoGAac7c\neQyv4Pny5psBwg4lJ0HSoRY/bMMQSOYz6BNV/6IKwzbd4robOw3LeyjJrj5vgf34\nFih+FsXc2zLgcx6/D7rgKlm76LmKSENx3yIAISrg5iZhe7aswZywacaukGYLovkH\nLf5B3ADoN+Felf1petUeoPWWc7V5fDNDoADsrSsCgYEAxdXY+bt1RJ4x6sZyZeri\n7iNZxJbLfzP2dWNGh5baBgBdbnYyREse051SzkM2QhgIGtxmWagBm3azCOIH7wJt\nE+rbTftdZVsrJwQG3DpvDw8m/MXYet5fqNAOurnp4oMGGgDvyHdrPO2Ys4Id2BfC\nrX1KptaxyjECUeQ8aC4j4BM=\n-----END PRIVATE KEY-----\n",
#   "client_email": "firebase-adminsdk-8u2gz@shwipt-dev.iam.gserviceaccount.com",
#   "client_id": "111104411798375737583",
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-8u2gz%40shwipt-dev.iam.gserviceaccount.com"
# })

# default_app = initialize_app(creds)