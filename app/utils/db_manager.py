# app/utils/db_manager.py
import os
from datetime import datetime, timezone

import os
import boto3
from botocore.exceptions import ClientError

try:
    import streamlit as st
    _SECRETS = dict(st.secrets)
except Exception:
    _SECRETS = {}

# --- Credential loading fallback chain ---
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or _SECRETS.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or _SECRETS.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION") or _SECRETS.get("AWS_DEFAULT_REGION", "ap-southeast-2")
DDB_TABLE_NAME = os.getenv("DDB_TABLE_NAME") or _SECRETS.get("DDB_TABLE_NAME", "marketing_names")

# --- Create boto3 session explicitly ---
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError("❌ Missing AWS credentials. Please set them in Streamlit secrets or environment variables.")

_session = boto3.session.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)
_dynamodb = _session.resource("dynamodb")
_ddb_client = _session.client("dynamodb")



def _table_exists(table_name: str) -> bool:
    try:
        _ddb_client.describe_table(TableName=table_name)
        return True
    except _ddb_client.exceptions.ResourceNotFoundException:
        return False


def init_db():
    """
    Create the DynamoDB table with a GSI if it doesn't exist.
    - PK: name (S)
    - GSI: by_planner_type (planner_type as HASH)
    Billing: PAY_PER_REQUEST
    """
    if _table_exists(DDB_TABLE_NAME):
        return

    _ddb_client.create_table(
        TableName=DDB_TABLE_NAME,
        AttributeDefinitions=[
            {"AttributeName": "name", "AttributeType": "S"},
            {"AttributeName": "planner_type", "AttributeType": "S"},  # for GSI
        ],
        KeySchema=[
            {"AttributeName": "name", "KeyType": "HASH"},
        ],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_planner_type",
                "KeySchema": [{"AttributeName": "planner_type", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},  # simplest; includes all attrs
            }
        ],
        Tags=[{"Key": "app", "Value": "naming-planner"}],
    )

    waiter = _ddb_client.get_waiter("table_exists")
    waiter.wait(TableName=DDB_TABLE_NAME)


def _get_table():
    return _dynamodb.Table(DDB_TABLE_NAME)


def insert_name(record: dict):
    """
    Insert new record, enforcing uniqueness on 'name'.
    - Uses ConditionExpression to avoid overwriting existing item with same name.
    """
    table = _get_table()
    item = {
        # Keys
        "name": record.get("name"),  # PK, must be unique
        # Attributes (Dynamo is schemaless; store as strings where appropriate)
        "planner_type": record.get("planner_type"),
        "plan_number": record.get("plan_number"),
        "advertiser": record.get("advertiser"),
        "product": record.get("product"),
        "objective": record.get("objective"),
        "campaign": record.get("campaign"),
        "month": record.get("month"),
        "year": record.get("year"),
        "strategy_tactic": record.get("strategy_tactic"),
        "publisher": record.get("publisher"),
        "site": record.get("site"),
        "media_type": record.get("media_type"),
        "targeting": record.get("targeting"),
        "size_format": record.get("size_format"),
        "creative_message": record.get("creative_message"),
        "free_form": record.get("free_form"),
        "source": record.get("source"),
        "validation_status": record.get("validation_status"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Remove None so we don't store empty attributes
    item = {k: v for k, v in item.items() if v is not None}

    if not item.get("name"):
        raise ValueError("insert_name() requires 'name' in record")

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(#n)",  # uniqueness guard
            ExpressionAttributeNames={"#n": "name"},
        )
        print(f"✅ Saved '{item['name']}' successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"⚠️ Record with name '{item['name']}' already exists.")
        else:
            print(f"⚠️ Error inserting record: {e}")
            raise


def fetch_all_names(planner_type: str = None):
    """
    Fetch list of names.
    - If planner_type is provided: Query the GSI.
    - Else: Scan table with projection (only 'name'), paginating until done.
    """
    table = _get_table()

    if planner_type:
        # Query via GSI for efficiency
        from boto3.dynamodb.conditions import Key

        names = []
        kwargs = {
            "IndexName": "by_planner_type",
            "KeyConditionExpression": Key("planner_type").eq(planner_type),
            "ProjectionExpression": "#n",
            "ExpressionAttributeNames": {"#n": "name"},
        }
        while True:
            resp = table.query(**kwargs)
            names.extend(i["name"] for i in resp.get("Items", []) if "name" in i)
            if "LastEvaluatedKey" in resp:
                kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            else:
                break
        return names

    # No filter: full table scan with projection
    names = []
    kwargs = {
        "ProjectionExpression": "#n",
        "ExpressionAttributeNames": {"#n": "name"},
    }
    while True:
        resp = table.scan(**kwargs)
        names.extend(i["name"] for i in resp.get("Items", []) if "name" in i)
        if "LastEvaluatedKey" in resp:
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        else:
            break
    return names
