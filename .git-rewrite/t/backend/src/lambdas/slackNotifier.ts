import { SNSEvent, SNSEventRecord } from 'aws-lambda';

interface SlackMessage {
  text: string;
  channel?: string;
  username?: string;
  icon_emoji?: string;
  attachments?: Array<{
    color: string;
    title?: string;
    text?: string;
    fields?: Array<{
      title: string;
      value: string;
      short?: boolean;
    }>;
    ts?: number;
  }>;
}

/**
 * Lambda function to send CloudWatch alarms to Slack
 * Triggered by SNS when CloudWatch alarms fire
 */
export const handler = async (event: SNSEvent): Promise<void> => {
  console.log('Slack notifier received event:', JSON.stringify(event, null, 2));

  const slackWebhookUrl = process.env.SLACK_WEBHOOK_URL;
  const stage = process.env.STAGE || 'dev';

  if (!slackWebhookUrl || slackWebhookUrl === 'https://hooks.slack.com/services/XXX/YYY/ZZZ') {
    console.log('No Slack webhook URL configured, skipping notifications');
    return;
  }

  for (const record of event.Records) {
    try {
      await processAlarmRecord(record, slackWebhookUrl, stage);
    } catch (error) {
      console.error('Failed to process SNS record:', error);
    }
  }
};

async function processAlarmRecord(record: SNSEventRecord, webhookUrl: string, stage: string): Promise<void> {
  const message = JSON.parse(record.Sns.Message);
  
  // Parse CloudWatch alarm
  const alarmName = message.AlarmName || 'Unknown Alarm';
  const alarmDescription = message.AlarmDescription || 'No description';
  const newState = message.NewStateValue || 'UNKNOWN';
  const reason = message.NewStateReason || 'No reason provided';
  const region = message.Region || 'us-east-1';
  const accountId = message.AWSAccountId || 'Unknown';
  const timestamp = new Date(message.StateChangeTime || Date.now());

  // Determine severity and color
  const isError = newState === 'ALARM';
  const color = isError ? '#FF0000' : '#00FF00'; // Red for alarms, green for OK
  const emoji = isError ? '🚨' : '✅';
  const channel = isError ? '#ops-alerts' : '#ops-status';

  // Create rich Slack message
  const slackMessage: SlackMessage = {
    text: `${emoji} PetPlantr Alert [${stage.toUpperCase()}]`,
    channel,
    username: 'PetPlantr Monitor',
    icon_emoji: ':robot_face:',
    attachments: [
      {
        color,
        title: `${alarmName} - ${newState}`,
        text: alarmDescription,
        fields: [
          {
            title: 'Reason',
            value: reason,
            short: false
          },
          {
            title: 'Region',
            value: region,
            short: true
          },
          {
            title: 'Account',
            value: accountId,
            short: true
          },
          {
            title: 'Time',
            value: timestamp.toISOString(),
            short: true
          },
          {
            title: 'Stage',
            value: stage.toUpperCase(),
            short: true
          }
        ],
        ts: Math.floor(timestamp.getTime() / 1000)
      }
    ]
  };

  // Send to Slack
  const response = await fetch(webhookUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(slackMessage)
  });

  if (!response.ok) {
    throw new Error(`Slack API error: ${response.status} ${response.statusText}`);
  }

  console.log(`Slack notification sent for alarm: ${alarmName}`);
}
