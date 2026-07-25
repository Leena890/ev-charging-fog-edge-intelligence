import json
from decimal import Decimal
import boto3

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('EV_Station_Logs')

def decimal_convert(val):
    """DynamoDB requires float metrics to be converted to Decimal objects."""
    return Decimal(str(val))

def lambda_handler(event, context):
    """Loop through the batch of records sent by SQS and save to DynamoDB."""
    for record in event.get('Records', []):
        try:
            # SQS body payload arrives as a string; parse it back to a dictionary
            payload = json.loads(record['body'])

            station_id = payload['station_id']
            timestamp = payload['timestamp']
            sensors = payload['sensors']

            print(f"Processing logs for Station: {station_id} at {timestamp}")

            # Write structured item directly into DynamoDB
            table.put_item(
                Item={
                    'station_id': station_id,
                    'timestamp': timestamp,
                    'cable_temperature_celsius': decimal_convert(sensors['cable_temperature_celsius']),
                    'electrical_current_amperes': decimal_convert(sensors['electrical_current_amperes']),
                    'hydrogen_gas_ppm': decimal_convert(sensors['hydrogen_gas_ppm']),
                    'cooling_fan_speed_rpm': int(sensors['cooling_fan_speed_rpm'])
                }
            )
            print("Successfully written to DynamoDB!")

        except Exception as e:
            print(f"Error processing record: {str(e)}")
            raise e  # Raising exception informs SQS that message needs retry if failed

    return {
        'statusCode': 200,
        'body': json.dumps('Batch processed successfully!')
    }