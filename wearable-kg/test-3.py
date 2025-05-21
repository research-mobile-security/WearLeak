import csv
import os
import time 
from dotenv import load_dotenv
from neo4j import GraphDatabase
import json
load_dotenv()

# Neo4j Connection and Database Setup
def connect_neo4j(uri, username, password):
    return GraphDatabase.driver(uri, auth=(username, password))

def create_database_if_not_exists(driver, database_name):
    with driver.session(database="system") as session:
        db_exists = session.execute_read(check_database_exists_tx, database_name)
        if not db_exists:
            session.execute_write(create_database_tx, database_name)
            print(f"Database '{database_name}' created successfully!")
            time.sleep(5)  # Wait for the database to initialize
        else:
            print(f"Database '{database_name}' already exists.")

def check_database_exists_tx(tx, database_name):
    result = tx.run("SHOW DATABASES")
    databases = [record["name"] for record in result]
    return database_name in databases

def create_database_tx(tx, database_name):
    tx.run(f"CREATE DATABASE {database_name}")

# Utility to Execute Cypher Queries
def execute_query(driver, cypher_query, parameters=None, database="kgwearable"):
    try:
        with driver.session(database=database) as session:
            session.run(cypher_query, parameters)
    except Exception as e:
        print(f"Error executing query: {e}")

# Dynamic Node and Relationship Creation
def create_knowledge_graph(driver, json_data):
    root_id = json_data["_id"]

    # Root Node
    execute_query(driver, "MERGE (root:App {id: $id})", {"id": root_id})

    # Key-to-relationship mapping
    key_relationship_map = {
        "manifest_permission": "has_permission",
        "tag-meta-data": "has_metadata",
        "tag-property": "has_property",
        "tag-action": "request_action",
        "tag-application": "has_application",
        "tag-data": "has_data",
        "tag-provider": "has_provider",
        "tag-receiver": "has_receiver",
        "tag-service": "has_service",
        "tag-uses-feature": "has_feature",
        "tag-uses-library": "has_library",
        "data-shared": "share_data",
        "data-collected": "collect_data",
    }

    for key, relationship in key_relationship_map.items():
            cypher_query = f"""
                MERGE (node:{key.replace('-', '_').title()} {{name: $key}})
                MERGE (root:App {{id: $root_id}})
                MERGE (root)-[:{relationship.upper()}]->(node)
            """
            execute_query(driver, cypher_query, {"key": key, "root_id": root_id})
def insert_permissions_create_node(driver, permissions):
    """
    Insert permission data as nodes connected to the 'manifest_permission' node.
    
    Args:
        driver: The Neo4j driver instance.
        permissions: A list of permissions to insert.
    """
    cypher_query = """
    MATCH (mp:Manifest_Permission {name: "manifest_permission"})
    UNWIND $permissions AS permission
    MERGE (perm:Permission {name: permission})
    MERGE (mp)-[:CONTAIN_PERMISSION]->(perm)
    """
    try:
        with driver.session(database="kgwearable") as session:
            session.run(cypher_query, {"permissions": permissions})
        print("Permissions inserted successfully!")
    except Exception as e:
        print(f"Error inserting permissions: {e}")
def insert_permissions_non_create_node(driver, permissions):
    """
    Add permission data as a single property list in the 'manifest_permission' node.
    
    Args:
        driver: The Neo4j driver instance.
        permissions: A list of permissions to insert.
    """
    cypher_query = """
    MATCH (mp:Manifest_Permission {name: "manifest_permission"})
    SET mp.permissions = $permissions
    """
    try:
        with driver.session(database="kgwearable") as session:
            session.run(cypher_query, {"permissions": permissions})
        print("Permissions added to 'manifest_permission' node successfully!")
    except Exception as e:
        print(f"Error inserting permissions: {e}")
def insert_tag_actions_create_node(driver, tag_actions):
    """
    Insert tag-action data as nodes connected to the 'tag-action' node.
    
    Args:
        driver: The Neo4j driver instance.
        tag_actions: A list of dictionaries containing tag-action data.
    """
    cypher_query = """
    MATCH (ta:Tag_Action {name: "tag-action"})
    UNWIND $tag_actions AS action
    MERGE (actionNode:Action {name: action.name})
    MERGE (ta)-[:DO_ACTION]->(actionNode)
    """
    try:
        with driver.session(database="kgwearable") as session:
            session.run(cypher_query, {"tag_actions": tag_actions})
        print("Tag-actions inserted successfully!")
    except Exception as e:
        print(f"Error inserting tag-actions: {e}")
def insert_tag_actions_non_create_node(driver, tag_actions):
    """
    Add tag-action data as a single property list in the 'tag-action' node.
    
    Args:
        driver: The Neo4j driver instance.
        tag_actions: A list of dictionaries containing tag-action data.
    """
    # Trích xuất tên từ danh sách tag_actions
    tag_action_names = [action["name"] for action in tag_actions]

    cypher_query = """
    MATCH (ta:Tag_Action {name: "tag-action"})
    SET ta.actions = $tag_action_names
    """
    try:
        with driver.session(database="kgwearable") as session:
            session.run(cypher_query, {"tag_action_names": tag_action_names})
        print("Tag-actions added to 'tag-action' node successfully!")
    except Exception as e:
        print(f"Error inserting tag-actions: {e}")

# Main Script Execution
if __name__ == "__main__":
    # Connection Details
    NEO4J_URI = os.environ["NEO4J_URI"]
    NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
    NEO4J_DATABASE = "kgwearable"
    NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
    AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

    # Connect to Neo4j
    driver = connect_neo4j(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    # Ensure Database Exists
    create_database_if_not_exists(driver, NEO4J_DATABASE)

    # JSON Data
    json_data = json_data = {
        '_id': 'xyz.klinker.messenger',
        'manifest_permission': [],
        "tag-meta-data": [],
        "tag-property": [],
        'tag-action': [],
        'tag-application': [],
        'tag-data': [],
        'tag-provider': [],
        'tag-receiver': [],
        'tag-service': [],
        'tag-uses-feature': [],
        'tag-uses-library': [],
        'data-shared': [],
        'data-collected': []
    }

    # Create the Knowledge Graph
    create_knowledge_graph(driver, json_data)
    #
    # permissions_data = [
    #     'android.permission.SEND_SMS', 'android.permission.READ_SMS', 'android.permission.WRITE_SMS',
    #     'android.permission.RECEIVE_SMS', 'android.permission.RECEIVE_MMS', 'android.permission.READ_CONTACTS',
    #     'android.permission.READ_PROFILE', 'android.permission.READ_PHONE_STATE', 'android.provider.Telephony.SMS_RECEIVED',
    #     'android.permission.WAKE_LOCK', 'android.permission.INTERNET', 'android.permission.CHANGE_NETWORK_STATE',
    #     'android.permission.ACCESS_NETWORK_STATE', 'android.permission.CAMERA', 'android.permission.READ_EXTERNAL_STORAGE',
    #     'android.permission.WRITE_EXTERNAL_STORAGE', 'android.permission.RECORD_AUDIO', 'android.permission.RECEIVE_BOOT_COMPLETED',
    #     'android.permission.ACCESS_COARSE_LOCATION', 'android.permission.ACCESS_FINE_LOCATION', 'android.permission.SYSTEM_ALERT_WINDOW',
    #     'android.permission.CALL_PHONE', 'com.google.android.c2dm.permission.RECEIVE', 'com.google.android.providers.gsf.permission.READ_GSERVICES',
    #     'android.permission.USE_FINGERPRINT', 'android.permission.FOREGROUND_SERVICE', 'android.permission.READ_MEDIA_IMAGES',
    #     'android.permission.READ_MEDIA_VIDEO', 'android.permission.FOREGROUND_SERVICE_DATA_SYNC', 'android.permission.SCHEDULE_EXACT_ALARM',
    #     'android.permission.WRITE_SETTINGS', 'com.android.launcher.permission.INSTALL_SHORTCUT', 'android.permission.POST_NOTIFICATIONS',
    #     'android.permission.ACCESS_WIFI_STATE', 'android.permission.ACCESS_ADSERVICES_ATTRIBUTION', 'com.google.android.gms.permission.AD_ID',
    #     'com.huawei.appmarket.service.commondata.permission.GET_COMMON_DATA', 'android.permission.ACCESS_ADSERVICES_TOPICS',
    #     'android.permission.ACCESS_ADSERVICES_AD_ID', 'android.permission.USE_BIOMETRIC', 'com.android.vending.BILLING',
    #     'com.applovin.array.apphub.permission.BIND_APPHUB_SERVICE', 'com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE',
    #     'xyz.klinker.messenger.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION', 'com.sec.android.provider.badge.permission.READ',
    #     'com.sec.android.provider.badge.permission.WRITE', 'com.htc.launcher.permission.READ_SETTINGS', 'com.htc.launcher.permission.UPDATE_SHORTCUT',
    #     'com.sonyericsson.home.permission.BROADCAST_BADGE', 'com.sonymobile.home.permission.PROVIDER_INSERT_BADGE',
    #     'com.anddoes.launcher.permission.UPDATE_COUNT', 'com.majeur.launcher.permission.UPDATE_BADGE', 'com.huawei.android.launcher.permission.CHANGE_BADGE',
    #     'com.huawei.android.launcher.permission.READ_SETTINGS', 'com.huawei.android.launcher.permission.WRITE_SETTINGS',
    #     'android.permission.READ_APP_BADGE', 'com.oppo.launcher.permission.READ_SETTINGS', 'com.oppo.launcher.permission.WRITE_SETTINGS',
    #     'me.everything.badger.permission.BADGE_COUNT_READ', 'me.everything.badger.permission.BADGE_COUNT_WRITE'
    # ]

    # # Insert permissions into Neo4j
    # # insert_permissions_create_node(driver, permissions_data)
    # insert_permissions_non_create_node(driver, permissions_data)
    # tag_action_data = [
    #     {'name': 'android.intent.action.SENDTO'},
    #     {'name': 'com.appsflyer.referrer.INSTALL_PROVIDER'},
    #     {'name': 'androidx.browser.customtabs.CustomTabsService'},
    #     {'name': 'android.intent.action.VIEW'},
    #     {'name': 'android.intent.action.ACTION_VIEW'},
    #     {'name': 'android.support.customtabs.action.CustomTabsService'},
    #     {'name': 'android.intent.action.INSERT'},
    #     {'name': 'com.android.vending.billing.InAppBillingService.BIND'},
    #     {'name': 'com.applovin.am.intent.action.APPHUB_SERVICE'},
    #     {'name': 'com.digitalturbine.ignite.cl.IgniteRemoteService'},
    #     {'name': 'android.intent.action.MAIN'},
    #     {'name': 'android.intent.action.SEND'},
    #     {'name': 'android.intent.action.SEND_MULTIPLE'},
    #     {'name': 'android.intent.action.CREATE_SHORTCUT'},
    #     {'name': 'android.service.quicksettings.action.QS_TILE'},
    #     {'name': 'android.provider.Telephony.SMS_DELIVER'},
    #     {'name': 'android.provider.Telephony.SMS_RECEIVED'},
    #     {'name': 'android.provider.Telephony.WAP_PUSH_DELIVER'},
    #     {'name': 'xyz.klinker.messenger.CAR_REPLY'},
    #     {'name': 'com.google.android.c2dm.intent.RECEIVE'},
    #     {'name': 'com.google.android.exoplayer.downloadService.action.RESTART'},
    #     {'name': 'android.intent.action.ACTION_POWER_CONNECTED'},
    #     {'name': 'android.intent.action.ACTION_POWER_DISCONNECTED'},
    #     {'name': 'android.intent.action.BATTERY_OKAY'},
    #     {'name': 'android.net.conn.CONNECTIVITY_CHANGE'},
    #     {'name': 'androidx.work.impl.background.systemalarm.UpdateProxies'},
    #     {'name': 'android.service.chooser.ChooserTargetService'},
    #     {'name': 'androidx.profileinstaller.action.INSTALL_PROFILE'},
    #     {'name': 'androidx.profileinstaller.action.SKIP_FILE'},
    #     {'name': 'androidx.profileinstaller.action.SAVE_PROFILE'}
    # ]

    # # # Insert tag-actions into Neo4j
    # # insert_tag_actions(driver, tag_action_data)
    # insert_tag_actions_non_create_node(driver, tag_action_data)
    # Close the Driver
    driver.close()
# def insert_data_to_node(driver, node_name, data):
#     """
#     Add data directly to the specified node in Neo4j.
    
#     Args:
#         driver: The Neo4j driver instance.
#         node_name: The name of the node (e.g., 'manifest_permission').
#         data: The data to add (list, dictionary, or string).
#     """
#     cypher_query = f"""
#     MATCH (node:{node_name.replace('-', '_').title()} {{name: $node_name}})
#     SET node.data = $data
#     """
#     try:
#         with driver.session(database="kgwearable") as session:
#             session.run(cypher_query, {"node_name": node_name, "data": data})
#         print(f"Data added to '{node_name}' node successfully!")
#     except Exception as e:
#         print(f"Error adding data to '{node_name}' node: {e}")
def insert_data_to_node(driver, node_name, data):
    """
    Add data directly to the specified node in Neo4j.
    
    Args:
        driver: The Neo4j driver instance.
        node_name: The name of the node (e.g., 'manifest_permission').
        data: The data to add (list, dictionary, or string).
    """
    # Convert nested dictionaries or lists to JSON strings for storage
    if isinstance(data, (dict, list)):
        data = json.dumps(data)  # Convert to JSON string

    cypher_query = f"""
    MATCH (node:{node_name.replace('-', '_').title()} {{name: $node_name}})
    SET node.data = $data
    """
    try:
        with driver.session(database="kgwearable") as session:
            session.run(cypher_query, {"node_name": node_name, "data": data})
        print(f"Data added to '{node_name}' node successfully!")
    except Exception as e:
        print(f"Error adding data to '{node_name}' node: {e}")
json_data = {'_id': 'xyz.klinker.messenger', 'manifest_permission': ['android.permission.SEND_SMS', 'android.permission.READ_SMS', 'android.permission.WRITE_SMS', 'android.permission.RECEIVE_SMS', 'android.permission.RECEIVE_MMS', 'android.permission.READ_CONTACTS', 'android.permission.READ_PROFILE', 'android.permission.READ_PHONE_STATE', 'android.provider.Telephony.SMS_RECEIVED', 'android.permission.WAKE_LOCK', 'android.permission.INTERNET', 'android.permission.CHANGE_NETWORK_STATE', 'android.permission.ACCESS_NETWORK_STATE', 'android.permission.CAMERA', 'android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE', 'android.permission.RECORD_AUDIO', 'android.permission.RECEIVE_BOOT_COMPLETED', 'android.permission.ACCESS_COARSE_LOCATION', 'android.permission.ACCESS_FINE_LOCATION', 'android.permission.SYSTEM_ALERT_WINDOW', 'android.permission.CALL_PHONE', 'com.google.android.c2dm.permission.RECEIVE', 'com.google.android.providers.gsf.permission.READ_GSERVICES', 'android.permission.USE_FINGERPRINT', 'android.permission.FOREGROUND_SERVICE', 'android.permission.READ_MEDIA_IMAGES', 'android.permission.READ_MEDIA_VIDEO', 'android.permission.FOREGROUND_SERVICE_DATA_SYNC', 'android.permission.SCHEDULE_EXACT_ALARM', 'android.permission.WRITE_SETTINGS', 'com.android.launcher.permission.INSTALL_SHORTCUT', 'android.permission.POST_NOTIFICATIONS', 'android.permission.ACCESS_WIFI_STATE', 'android.permission.ACCESS_ADSERVICES_ATTRIBUTION', 'com.google.android.gms.permission.AD_ID', 'com.huawei.appmarket.service.commondata.permission.GET_COMMON_DATA', 'android.permission.ACCESS_ADSERVICES_TOPICS', 'android.permission.ACCESS_ADSERVICES_AD_ID', 'android.permission.USE_BIOMETRIC', 'com.android.vending.BILLING', 'com.applovin.array.apphub.permission.BIND_APPHUB_SERVICE', 'com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE', 'xyz.klinker.messenger.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION', 'com.sec.android.provider.badge.permission.READ', 'com.sec.android.provider.badge.permission.WRITE', 'com.htc.launcher.permission.READ_SETTINGS', 'com.htc.launcher.permission.UPDATE_SHORTCUT', 'com.sonyericsson.home.permission.BROADCAST_BADGE', 'com.sonymobile.home.permission.PROVIDER_INSERT_BADGE', 'com.anddoes.launcher.permission.UPDATE_COUNT', 'com.majeur.launcher.permission.UPDATE_BADGE', 'com.huawei.android.launcher.permission.CHANGE_BADGE', 'com.huawei.android.launcher.permission.READ_SETTINGS', 'com.huawei.android.launcher.permission.WRITE_SETTINGS', 'android.permission.READ_APP_BADGE', 'com.oppo.launcher.permission.READ_SETTINGS', 'com.oppo.launcher.permission.WRITE_SETTINGS', 'me.everything.badger.permission.BADGE_COUNT_READ', 'me.everything.badger.permission.BADGE_COUNT_WRITE'], 'tag-action': [{'name': 'android.intent.action.SENDTO'}, {'name': 'com.appsflyer.referrer.INSTALL_PROVIDER'}, {'name': 'androidx.browser.customtabs.CustomTabsService'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.ACTION_VIEW'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.support.customtabs.action.CustomTabsService'}, {'name': 'android.intent.action.INSERT'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.DIAL'}, {'name': 'com.android.vending.billing.InAppBillingService.BIND'}, {'name': 'com.applovin.am.intent.action.APPHUB_SERVICE'}, {'name': 'com.digitalturbine.ignite.cl.IgniteRemoteService'}, {'name': 'android.intent.action.MAIN'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.MAIN'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.MAIN'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.SEND'}, {'name': 'android.intent.action.SENDTO'}, {'name': 'android.intent.action.SEND'}, {'name': 'android.intent.action.SEND'}, {'name': 'android.intent.action.SEND_MULTIPLE'}, {'name': 'android.intent.action.SEND'}, {'name': 'android.intent.action.CREATE_SHORTCUT'}, {'name': 'android.appwidget.action.APPWIDGET_CONFIGURE'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.service.quicksettings.action.QS_TILE'}, {'name': 'android.appwidget.action.APPWIDGET_UPDATE'}, {'name': 'android.appwidget.action.APPWIDGET_UPDATE'}, {'name': 'android.provider.Telephony.SMS_DELIVER'}, {'name': 'android.provider.Telephony.SMS_RECEIVED'}, {'name': 'android.provider.Telephony.WAP_PUSH_DELIVER'}, {'name': 'android.intent.action.BOOT_COMPLETED'}, {'name': 'android.intent.action.MY_PACKAGE_REPLACED'}, {'name': 'xyz.klinker.messenger.CAR_REPLY'}, {'name': 'xyz.klinker.messenger.CAR_READ'}, {'name': 'android.intent.action.RESPOND_VIA_MESSAGE'}, {'name': 'com.google.android.apps.dashclock.Extension'}, {'name': 'android.service.quicksettings.action.QS_TILE'}, {'name': 'com.google.firebase.MESSAGING_EVENT'}, {'name': 'com.google.firebase.MESSAGING_EVENT'}, {'name': 'android.intent.action.VIEW'}, {'name': 'android.intent.action.VIEW'}, {'name': 'com.google.android.c2dm.intent.RECEIVE'}, {'name': 'com.google.firebase.MESSAGING_EVENT'}, {'name': 'com.google.android.exoplayer.downloadService.action.RESTART'}, {'name': 'android.intent.action.ACTION_POWER_CONNECTED'}, {'name': 'android.intent.action.ACTION_POWER_DISCONNECTED'}, {'name': 'android.intent.action.BATTERY_OKAY'}, {'name': 'android.intent.action.BATTERY_LOW'}, {'name': 'android.intent.action.DEVICE_STORAGE_LOW'}, {'name': 'android.intent.action.DEVICE_STORAGE_OK'}, {'name': 'android.net.conn.CONNECTIVITY_CHANGE'}, {'name': 'android.intent.action.BOOT_COMPLETED'}, {'name': 'android.intent.action.TIME_SET'}, {'name': 'android.intent.action.TIMEZONE_CHANGED'}, {'name': 'androidx.work.impl.background.systemalarm.UpdateProxies'}, {'name': 'androidx.work.diagnostics.REQUEST_DIAGNOSTICS'}, {'name': 'androidx.core.content.pm.SHORTCUT_LISTENER'}, {'name': 'android.service.chooser.ChooserTargetService'}, {'name': 'androidx.profileinstaller.action.INSTALL_PROFILE'}, {'name': 'androidx.profileinstaller.action.SKIP_FILE'}, {'name': 'androidx.profileinstaller.action.SAVE_PROFILE'}, {'name': 'androidx.profileinstaller.action.BENCHMARK_OPERATION'}, {'name': 'android.net.conn.CONNECTIVITY_CHANGE'}, {'name': 'com.ogury.sdk.intent.ENABLE_LOGS'}], 'tag-application': [{'theme': '@7F1501DF', 'label': '@7F1400B2', 'icon': '@7F110002', 'name': 'xyz.klinker.messenger.MessengerApplication', 'allowBackup': 'false', 'hardwareAccelerated': 'true', 'largeHeap': 'true', 'supportsRtl': 'true', 'banner': '@7F110001', 'extractNativeLibs': 'false', 'fullBackupContent': '@7F180003', 'networkSecurityConfig': '@7F180012', 'appCategory': '4', 'appComponentFactory': 'androidx.core.app.CoreComponentFactory'}], 'tag-data': [{'scheme': 'smsto', 'host': '*'}, {'scheme': 'https'}, {'scheme': 'http'}, {'scheme': 'market'}, {'scheme': 'https'}, {'scheme': 'http'}, {'scheme': 'https'}, {'mimeType': 'vnd.android.cursor.dir/event'}, {'scheme': 'sms'}, {'path': 'tel:'}, {'scheme': 'pulsesms'}, {'host': 'open'}, {'host': 'subscribe'}, {'scheme': 'https', 'host': 'pulsesms.onelink.me'}, {'scheme': 'sms'}, {'scheme': 'smsto'}, {'scheme': 'mms'}, {'scheme': 'mmsto'}, {'mimeType': 'text/vcard'}, {'mimeType': 'text/x-vcard'}, {'mimeType': 'text/plain'}, {'mimeType': 'image/*'}, {'mimeType': 'audio/*'}, {'mimeType': 'video/*'}, {'mimeType': 'image/*'}, {'mimeType': 'text/plain'}, {'mimeType': 'image/*'}, {'mimeType': 'audio/*'}, {'mimeType': 'video/*'}, {'scheme': 'pulse', 'host': 'sms-debug'}, {'mimeType': 'application/vnd.wap.mms-message'}, {'mimeType': 'application/vnd.wap.sic'}, {'scheme': 'sms'}, {'scheme': 'smsto'}, {'scheme': 'mms'}, {'scheme': 'mmsto'}, {'scheme': 'genericidp', 'host': 'firebase.auth', 'path': '/'}, {'scheme': 'recaptcha', 'host': 'firebase.auth', 'path': '/'}], 'tag-property': 'not-found', 'tag-provider': [{'name': 'androidx.core.content.FileProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.provider', 'grantUriPermissions': 'true'}, {'name': 'com.maplemedia.trumpet.broadcasts.MM_ContentProvider', 'enabled': 'true', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.MM_ContentProvider', 'initOrder': '1000'}, {'name': 'com.maplemedia.ivorysdk.onetrust.OneTrustModuleBridgeInitProvider', 'enabled': 'true', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.OneTrustModuleBridgeInitProvider', 'initOrder': '500'}, {'name': 'com.maplemedia.ivorysdk.max.MAXAdModuleInitProvider', 'enabled': 'true', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.MAXAdModuleInitProvider'}, {'name': 'com.squareup.picasso.PicassoProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.com.squareup.picasso'}, {'name': 'androidx.startup.InitializationProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.androidx-startup', 'initOrder': '-2147483648'}, {'name': 'com.maplemedia.ivorysdk.firebase.FirebaseModuleBridgeInitProvider', 'enabled': 'true', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.FirebaseModuleBridgeInitProvider', 'initOrder': '500'}, {'name': 'com.mobilefuse.sdk.MobileFuseSdkInitProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.mobilefusesdkinitprovider'}, {'name': 'com.google.android.gms.ads.MobileAdsInitProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.mobileadsinitprovider', 'initOrder': '100'}, {'name': 'com.maplemedia.ivorysdk.core.PlatformHelperInitProvider', 'enabled': 'true', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.PlatformHelperInitProvider', 'initOrder': '1000'}, {'name': 'com.applovin.sdk.AppLovinInitProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.applovininitprovider', 'initOrder': '101'}, {'name': 'com.google.firebase.provider.FirebaseInitProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.firebaseinitprovider', 'initOrder': '100', 'directBootAware': 'true'}, {'name': 'com.klinker.android.send_message.MmsFileProvider', 'enabled': 'true', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.MmsFileProvider', 'grantUriPermissions': 'true'}, {'name': 'io.maplemedia.commons.android.MM_FileProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.io.maplemedia.commons.android.library.fileprovider', 'grantUriPermissions': 'true'}, {'name': 'com.facebook.ads.AudienceNetworkContentProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.AudienceNetworkContentProvider'}, {'name': 'com.smaato.sdk.core.lifecycle.ProcessLifecycleOwnerInitializer', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.smaato-lifecycle-process'}, {'name': 'com.ironsource.lifecycle.IronsourceLifecycleProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.IronsourceLifecycleProvider'}], 'tag-receiver': [{'name': 'xyz.klinker.messenger.shared.widget.MessengerAppWidgetProvider', 'exported': 'true'}, {'name': 'xyz.klinker.messenger.shared.widget.shortcuts.ShortcutsWidgetProvider', 'exported': 'true'}, {'name': 'xyz.klinker.messenger.shared.receiver.SmsReceivedReceiver', 'permission': 'android.permission.BROADCAST_SMS', 'exported': 'true'}, {'name': 'xyz.klinker.messenger.shared.receiver.SmsReceivedNonDefaultReceiver', 'permission': 'android.permission.BROADCAST_SMS', 'exported': 'true'}, {'name': 'xyz.klinker.messenger.shared.receiver.SmsSentReceiver', 'exported': 'true', 'taskAffinity': 'xyz.klinker.messenger.SMS_SENT'}, {'name': 'xyz.klinker.messenger.shared.receiver.SmsSentReceiverNoRetry', 'exported': 'true'}, {'name': 'xyz.klinker.messenger.shared.receiver.SmsDeliveredReceiver', 'exported': 'true', 'taskAffinity': 'xyz.klinker.messenger.SMS_DELIVERED'}, {'name': 'com.android.mms.transaction.PushReceiver', 'permission': 'android.permission.BROADCAST_WAP_PUSH', 'exported': 'true'}, {'name': 'xyz.klinker.messenger.shared.receiver.MmsSentReceiver', 'exported': 'true', 'taskAffinity': 'com.klinker.android.messaging.MMS_SENT'}, {'name': 'xyz.klinker.messenger.shared.receiver.MmsReceivedReceiver', 'exported': 'true', 'taskAffinity': 'com.klinker.android.messaging.MMS_RECEIVED'}, {'name': 'xyz.klinker.messenger.shared.receiver.BootCompletedReceiver', 'exported': 'true'}, {'name': 'xyz.klinker.messenger.shared.service.jobs.ScheduledMessageJob', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.service.jobs.RepeatNotificationJob', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.NotificationDismissedReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.service.NotificationDismissedReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.NotificationMarkReadReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.NotificationMuteReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.NotificationCallReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.NotificationCopyOtpReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.NotificationArchiveReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.SendSmartReplyReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.notification_action.NotificationDeleteReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.CarReplyReceiver', 'exported': 'false'}, {'name': 'xyz.klinker.messenger.shared.receiver.CarReadReceiver', 'exported': 'false'}, {'name': 'com.google.firebase.iid.FirebaseInstanceIdReceiver', 'permission': 'com.google.android.c2dm.permission.SEND', 'exported': 'true'}, {'name': 'androidx.work.impl.utils.ForceStopRunnable$BroadcastReceiver', 'enabled': 'true', 'exported': 'false', 'directBootAware': 'false'}, {'name': 'androidx.work.impl.background.systemalarm.ConstraintProxy$BatteryChargingProxy', 'enabled': 'false', 'exported': 'false', 'directBootAware': 'false'}, {'name': 'androidx.work.impl.background.systemalarm.ConstraintProxy$BatteryNotLowProxy', 'enabled': 'false', 'exported': 'false', 'directBootAware': 'false'}, {'name': 'androidx.work.impl.background.systemalarm.ConstraintProxy$StorageNotLowProxy', 'enabled': 'false', 'exported': 'false', 'directBootAware': 'false'}, {'name': 'androidx.work.impl.background.systemalarm.ConstraintProxy$NetworkStateProxy', 'enabled': 'false', 'exported': 'false', 'directBootAware': 'false'}, {'name': 'androidx.work.impl.background.systemalarm.RescheduleReceiver', 'enabled': 'false', 'exported': 'false', 'directBootAware': 'false'}, {'name': 'androidx.work.impl.background.systemalarm.ConstraintProxyUpdateReceiver', 'enabled': '@7F050006', 'exported': 'false', 'directBootAware': 'false'}, {'name': 'androidx.work.impl.diagnostics.DiagnosticsReceiver', 'permission': 'android.permission.DUMP', 'enabled': 'true', 'exported': 'true', 'directBootAware': 'false'}, {'name': 'com.google.android.gms.measurement.AppMeasurementReceiver', 'enabled': 'true', 'exported': 'false'}, {'name': 'net.pubnative.lite.sdk.receiver.VolumeChangedActionReceiver'}, {'name': 'androidx.profileinstaller.ProfileInstallReceiver', 'permission': 'android.permission.DUMP', 'enabled': 'true', 'exported': 'true', 'directBootAware': 'false'}, {'name': 'com.google.android.datatransport.runtime.scheduling.jobscheduling.AlarmManagerSchedulerBroadcastReceiver', 'exported': 'false'}, {'name': 'com.mbridge.msdk.foundation.same.broadcast.NetWorkChangeReceiver', 'exported': 'true'}, {'name': 'com.ogury.core.internal.LogEnablerReceiver', 'enabled': 'true', 'exported': 'true'}], 'tag-service': 'not-found', 'tag-uses-feature': [{'name': 'android.hardware.camera', 'required': 'false'}, {'name': 'android.hardware.microphone', 'required': 'false'}, {'name': 'android.hardware.telephony', 'required': 'false'}, {'name': 'android.hardware.location', 'required': 'false'}, {'name': 'android.hardware.location.network', 'required': 'false'}, {'name': 'android.hardware.location.gps', 'required': 'false'}, {'name': 'android.software.leanback', 'required': 'false'}, {'name': 'android.hardware.touchscreen', 'required': 'false'}, {'name': 'android.software.app_widget', 'required': 'false'}, {'name': 'android.hardware.screen.portrait', 'required': 'false'}, {'name': 'android.hardware.screen.landscape', 'required': 'false'}, {'glEsVersion': '0x00020000', 'required': 'true'}], 'tag-uses-library': [{'name': 'com.sec.android.app.multiwindow', 'required': 'false'}, {'name': 'org.apache.http.legacy', 'required': 'false'}, {'name': 'androidx.window.extensions', 'required': 'false'}, {'name': 'androidx.window.sidecar', 'required': 'false'}, {'name': 'android.ext.adservices', 'required': 'false'}], 'data-shared': 'No information', 'data-collected': ['Audio', 'Personal info', 'Photos and videos', 'Contacts', 'App info and performance', 'Files and docs', 'Messages', 'Device or other IDs'], 'tag-meta-data': [{'name': 'com.google.android.gms.car.application', 'resource': '@7F180005'}, {'name': 'android.app.shortcuts', 'resource': '@7F18001E'}, {'name': 'android.service.chooser.chooser_target_service', 'value': 'androidx.sharetarget.ChooserTargetServiceCompat'}, {'name': 'android.appwidget.provider', 'resource': '@7F180004'}, {'name': 'android.appwidget.provider', 'resource': '@7F18001F'}, {'name': 'com.sec.android.support.multiwindow', 'value': 'true'}, {'name': 'com.sec.android.multiwindow.DEFAULT_SIZE_W', 'resource': '@7F070523'}, {'name': 'com.sec.android.multiwindow.DEFAULT_SIZE_H', 'resource': '@7F070522'}, {'name': 'com.sec.android.multiwindow.MINIMUM_SIZE_W', 'resource': '@7F070525'}, {'name': 'com.sec.android.multiwindow.MINIMUM_SIZE_H', 'resource': '@7F070524'}, {'name': 'ivory_activity_whitelist', 'value': 'activity.MessengerActivity,                 activity.InitialLoadActivity,                 premium.discount.DiscountActivity,                 premium.PurchaseActivity,                 com.maplemedia.trumpet.ui.expanded.TrumpetExpandedScreenActivity,                 com.maplemedia.trumpet.ui.newsfeed.TrumpetNewsfeedActivity'}, {'name': 'com.google.android.gms.ads.APPLICATION_ID', 'value': 'ca-app-pub-4229758926684576~9488586941'}, {'name': 'com.google.android.gms.ads.AD_MANAGER_APP', 'value': 'true'}, {'name': 'APSApplicationId', 'value': '544f7e55-53b7-4306-b8a4-b363879c7391'}, {'name': 'android.support.FILE_PROVIDER_PATHS', 'resource': '@7F180014'}, {'name': 'com.google.android.geo.API_KEY', 'value': 'AIzaSyBg-de2pZC1JTdIEidArhOpSRs_AmxNomY'}, {'name': 'com.google.android.gms.version', 'value': '@7F0C000E'}, {'name': 'protocolVersion', 'value': '2'}, {'name': 'worldReadable', 'value': 'true'}, {'name': 'preloaded_fonts', 'resource': '@7F030028'}, {'name': 'androidx.lifecycle.ProcessLifecycleInitializer', 'value': 'androidx.startup'}, {'name': 'com.unity3d.services.core.configuration.AdsSdkInitializer', 'value': 'androidx.startup'}, {'name': 'com.moloco.sdk.internal.android_context.ApplicationContextStartupComponentInitialization', 'value': 'androidx.startup'}, {'name': 'androidx.work.WorkManagerInitializer', 'value': 'androidx.startup'}, {'name': 'androidx.emoji2.text.EmojiCompatInitializer', 'value': 'androidx.startup'}, {'name': 'androidx.profileinstaller.ProfileInstallerInitializer', 'value': 'androidx.startup'}, {'name': 'firebase_messaging_auto_init_enabled', 'value': 'false'}, {'name': 'firebase_analytics_collection_enabled', 'value': 'false'}, {'name': 'firebase_crashlytics_collection_enabled', 'value': 'false'}, {'name': 'firebase_performance_collection_enabled', 'value': 'false'}, {'name': 'google_analytics_default_allow_analytics_storage', 'value': 'false'}, {'name': 'google_analytics_default_allow_ad_storage', 'value': 'false'}, {'name': 'google_analytics_default_allow_ad_user_data', 'value': 'false'}, {'name': 'google_analytics_default_allow_ad_personalization_signals', 'value': 'false'}, {'name': 'com.google.firebase.components:com.google.firebase.crashlytics.ndk.CrashlyticsNdkRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.crashlytics.FirebaseCrashlyticsKtxRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.crashlytics.CrashlyticsRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.auth.FirebaseAuthRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.messaging.FirebaseMessagingKtxRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.messaging.FirebaseMessagingRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.storage.FirebaseStorageKtxRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.storage.StorageRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.remoteconfig.FirebaseRemoteConfigKtxRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.remoteconfig.RemoteConfigRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.analytics.connector.internal.AnalyticsConnectorRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.sessions.FirebaseSessionsRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.installations.FirebaseInstallationsKtxRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.installations.FirebaseInstallationsRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.appcheck.FirebaseAppCheckKtxRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.appcheck.FirebaseAppCheckRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.ktx.FirebaseCommonLegacyRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.FirebaseCommonKtxRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.abt.component.AbtRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.firebase.components:com.google.firebase.datatransport.TransportRegistrar', 'value': 'com.google.firebase.components.ComponentRegistrar'}, {'name': 'com.google.android.gms.cloudmessaging.FINISHED_AFTER_HANDLED', 'value': 'true'}, {'name': 'com.mobilefuse.sdk.disable_auto_init', 'value': 'true'}, {'name': 'com.google.android.play.billingclient.version', 'value': '7.0.0'}, {'name': 'androidx.core.content.pm.shortcut_listener_impl', 'value': 'androidx.core.google.shortcuts.ShortcutInfoChangeListenerImpl'}, {'name': 'android.support.FILE_PROVIDER_PATHS', 'resource': '@7F18000F'}, {'name': 'backend:com.google.android.datatransport.cct.CctBackendFactory', 'value': 'cct'}, {'name': 'android.webkit.WebView.EnableSafeBrowsing', 'value': 'true'}, {'name': 'com.android.vending.splits.required', 'value': 'true'}, {'name': 'com.android.stamp.source', 'value': 'https://play.google.com/store'}, {'name': 'com.android.stamp.type', 'value': 'STAMP_TYPE_DISTRIBUTION_APK'}, {'name': 'com.android.vending.splits', 'resource': '@7F180020'}, {'name': 'com.android.vending.derived.apk.id', 'value': '4'}]}

# Add data to manifest_permission node
insert_data_to_node(driver, "manifest_permission", json_data["manifest_permission"])

# Add data to tag-meta-data node
insert_data_to_node(driver, "tag-meta-data", json_data["tag-meta-data"])

# Add data to tag-property node
insert_data_to_node(driver, "tag-property", json_data["tag-property"])

# Add data to tag-action node
insert_data_to_node(driver, "tag-action", json_data["tag-action"])

# Add data to tag-application node
insert_data_to_node(driver, "tag-application", json_data["tag-application"])

# Add data to tag-data node
insert_data_to_node(driver, "tag-data", json_data["tag-data"])

# Add data to tag-provider node
insert_data_to_node(driver, "tag-provider", json_data["tag-provider"])

# Add data to tag-receiver node
insert_data_to_node(driver, "tag-receiver", json_data["tag-receiver"])

# Add data to tag-service node
insert_data_to_node(driver, "tag-service", json_data["tag-service"])

# Add data to tag-uses-feature node
insert_data_to_node(driver, "tag-uses-feature", json_data["tag-uses-feature"])

# Add data to tag-uses-library node
insert_data_to_node(driver, "tag-uses-library", json_data["tag-uses-library"])

# Add data to data-shared node
insert_data_to_node(driver, "data-shared", json_data["data-shared"])

# Add data to data-collected node
insert_data_to_node(driver, "data-collected", json_data["data-collected"])
