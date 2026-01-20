import { getApiUrl, doExtrasFetch } from "../../../extensions.js";

const { eventSource, event_types } = SillyTavern.getContext();

let currentMessageId = null;
let accumulatedText = '';
let lastProcessedIndex = 0;
let isGenerating = false;
let lastText = '';
let pollInterval = null;
let lastMovementTime = 0;
const MOVEMENT_COOLDOWN = 2000;  // 2 seconds min between movements
const CHUNK_SIZE = 250;  // For fewer triggers and better context

// Function to send movement to Pi
async function sendMovement(head_pan, head_tilt, left_pan, left_tilt, right_pan, right_tilt) {
  const now = Date.now();
  if (now - lastMovementTime < MOVEMENT_COOLDOWN) return;  // Skip if too soon
  lastMovementTime = now;
  const piUrl = `http://192.168.1.51:5003/move?pan=${head_pan}&tilt=${head_tilt}&left_pan=${left_pan}&left_tilt=${left_tilt}&right_pan=${right_pan}&right_tilt=${right_tilt}`;
  try {
    await fetch(piUrl);
  } catch (error) {
    console.error('Movement request failed:', error);
  }
}

// Function to classify sentiment of a text chunk
async function classifySentiment(text) {
  if (!text.trim()) return null;

  try {
    const url = new URL(getApiUrl());
    url.pathname = '/api/classify';
    const classifyResult = await doExtrasFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        prompt: "Classify the emotion in this text from a depressed android's perspective, biasing toward sadness unless strongly otherwise: anger, disgust, fear, joy, neutral, sadness, surprise."  // Stronger bias prompt
      })
    });

    if (!classifyResult.ok) {
      throw new Error(`Classification failed with status: ${classifyResult.status}`);
    }

    const resultJson = await classifyResult.json();
    const classification = resultJson.classification;
    if (!classification || classification.length === 0) return 'sadness';

    // Sort by score descending if not already
    classification.sort((a, b) => b.score - a.score);
    let top = classification[0];

    // Threshold: If top score is low (<0.6), bias to sadness
    if (top.score < 0.6) {
      return 'sadness';
    }

    let sentiment = top.label.toLowerCase();  // Normalize case

    // Stronger bias for 'joy', 'surprise', 'neutral', and low-confidence 'anger'
    if (['joy', 'surprise', 'neutral'].includes(sentiment) || (sentiment === 'anger' && top.score < 0.4)) {
      const sadnessScore = classification.find(c => c.label.toLowerCase() === 'sadness')?.score || 0;
      const disgustScore = classification.find(c => c.label.toLowerCase() === 'disgust')?.score || 0;
      const angerScore = classification.find(c => c.label.toLowerCase() === 'anger')?.score || 0;
      if (sadnessScore > 0.1 || disgustScore > 0.1 || angerScore > 0.1) {
        return 'sadness';
      }
    }

    return sentiment;
  } catch (error) {
    console.error('Error during sentiment classification:', error);
    return 'sadness';  // Default bias
  }
}

// Function to map sentiment to movements (adjusted for j-hartmann model labels: anger, disgust, fear, joy, neutral, sadness, surprise)
function getMovementsForSentiment(sentiment) {
  let head_pan = 1500, head_tilt = 1500, left_pan = 1500, left_tilt = 1500, right_pan = 1500, right_tilt = 1500;
  switch (sentiment) {
    case 'sadness':
      head_tilt = 1800;  // Tilt head down
      left_tilt = 1200;  // Lower left arm tilt
      right_tilt = 1200; // Lower right arm tilt
      break;
    case 'joy':
      head_pan = 1200;  // Pan head left
      left_tilt = 1800;  // Raise left arm tilt
      right_tilt = 1800; // Raise right arm tilt
      break;
    case 'anger':
      head_pan = 1800;  // Pan head right
      right_pan = 2000;  // Extend right arm pan outward
      break;
    case 'fear':
      head_tilt = 1200;  // Tilt head up
      left_pan = 1000;   // Retract left arm pan
      right_pan = 1000;  // Retract right arm pan
      break;
    case 'surprise':
      head_pan = 1300;   // Slight head pan
      left_tilt = 2000;  // Raise left arm tilt high
      break;
    case 'disgust':
      head_tilt = 1600;  // Tilt head away
      right_tilt = 1000; // Lower right arm tilt
      break;
    default:
      // Neutral or unknown -> default to sadness pose
      head_tilt = 1800;  // Tilt head down
      left_tilt = 1200;  // Lower left arm tilt
      right_tilt = 1200; // Lower right arm tilt
      break;
  }
  return { head_pan, head_tilt, left_pan, left_tilt, right_pan, right_tilt };
}

// Function to process new text in larger chunks
async function processNewText(newText) {
  let remaining = newText;
  while (remaining.length >= CHUNK_SIZE) {
    const chunk = remaining.slice(0, CHUNK_SIZE).trim();
    if (chunk) {
      const sentiment = await classifySentiment(accumulatedText);  // Use full accumulated text for better context!
      if (sentiment) {
        const { head_pan, head_tilt, left_pan, left_tilt, right_pan, right_tilt } = getMovementsForSentiment(sentiment);
        await sendMovement(head_pan, head_tilt, left_pan, left_tilt, right_pan, right_tilt);
      }
    }
    remaining = remaining.slice(CHUNK_SIZE);
    lastProcessedIndex += CHUNK_SIZE;
  }
  // Handle trailing if significant
  if (remaining.length > CHUNK_SIZE / 2) {
    const sentiment = await classifySentiment(accumulatedText + remaining.trim());  // Include trailing for context
    if (sentiment) {
      const { head_pan, head_tilt, left_pan, left_tilt, right_pan, right_tilt } = getMovementsForSentiment(sentiment);
      await sendMovement(head_pan, head_tilt, left_pan, left_tilt, right_pan, right_tilt);
    }
    lastProcessedIndex += remaining.length;
  }
}

// Start polling for text changes during generation by checking the DOM
function startPolling() {
  if (pollInterval) return;
  pollInterval = setInterval(async () => {
    if (!isGenerating) return;

    const lastMes = $('#chat .mes:last');
    if (!lastMes.length || lastMes.hasClass('type_system') || lastMes.hasClass('is_user')) return;  // Skip if no message, system, or user

    const currentText = lastMes.find('.mes_text').text() || '';
    if (currentText.length <= lastText.length) return;

    const newText = currentText.slice(lastProcessedIndex);
    accumulatedText = currentText;
    lastText = currentText;

    await processNewText(newText);
  }, 300);  // Poll every 300ms
}

// Hook into generation start
eventSource.on(event_types.GENERATION_AFTER_COMMANDS || event_types.GENERATION_STARTED, (data) => {
  const context = SillyTavern.getContext();
  currentMessageId = context.chat.length;  // Next message index
  accumulatedText = '';
  lastProcessedIndex = 0;
  lastText = '';
  lastMovementTime = 0;
  isGenerating = true;
  startPolling();
  // Optional: Send neutral pose at start
  sendMovement(1500, 1500, 1500, 1500, 1500, 1500);
});

// Hook into message received to catch the final state if needed
eventSource.on(event_types.MESSAGE_RECEIVED, async (msgId) => {
  if (currentMessageId !== msgId) return;
  const context = SillyTavern.getContext();
  const message = context.chat[msgId];
  if (message && accumulatedText.length > lastProcessedIndex) {
    const remainingText = message.mes.slice(lastProcessedIndex);
    await processNewText(remainingText);
  }
});

// Hook into generation end
eventSource.on(event_types.GENERATION_ENDED, async () => {
  isGenerating = false;
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  // Process any final remaining text from DOM
  const lastMes = $('#chat .mes:last');
  if (lastMes.length) {
    const currentText = lastMes.find('.mes_text').text() || '';
    if (currentText.length > lastProcessedIndex) {
      const remainingText = currentText.slice(lastProcessedIndex);
      await processNewText(remainingText);
    }
  }
  // Process variables
  currentMessageId = null;
  accumulatedText = '';
  lastProcessedIndex = 0;
  lastText = '';
});
