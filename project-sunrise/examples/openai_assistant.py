"""
Connect to OpenAI Assistant, ask questions, and get AI analysis.
"""

import sys
import time
import json
from openai import OpenAI
import argparse


def load_questions(questions_file):
    """Load questions from file, ignoring comments."""
    questions = []
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    questions.append(line)
    except FileNotFoundError:
        print(f"Error: Questions file not found: {questions_file}", file=sys.stderr)
        sys.exit(1)
    
    return questions


def load_calendar_data(json_file):
    """Load calendar data to provide context."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def ask_assistant(client, assistant_id, question, calendar_context=None):
    """
    Ask OpenAI Assistant a question and wait for response.
    
    Args:
        client: OpenAI client instance
        assistant_id: The assistant ID to use
        question: The question to ask
        calendar_context: Optional calendar data for context
        
    Returns:
        Assistant's response text
    """
    print(f"Creating thread with assistant...", file=sys.stderr)
    
    # Create a thread
    thread = client.beta.threads.create()
    
    # Build message content with calendar context
    message_content = question
    
    if calendar_context:
        events = calendar_context.get('events', [])
        if events:
            context = "\n\nToday's USD Economic Calendar Events:\n"
            for event in events:
                time_str = event.get('time', 'TBA')
                event_name = event.get('event', '')
                impact = event.get('impact', '')
                forecast = event.get('forecast', '')
                previous = event.get('previous', '')
                context += f"- {time_str}: {event_name} (Impact: {impact}, Forecast: {forecast}, Previous: {previous})\n"
            
            message_content = context + "\n" + question
    
    # Add message to thread
    print(f"Sending question to assistant...", file=sys.stderr)
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_content
    )
    
    # Run the assistant
    print(f"Running assistant (this may take 10-30 seconds)...", file=sys.stderr)
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion
    max_wait = 60  # Maximum 60 seconds
    start_time = time.time()
    
    while True:
        if time.time() - start_time > max_wait:
            print("Error: Assistant response timed out", file=sys.stderr)
            return None
        
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        
        status = run_status.status
        print(f"Status: {status}...", file=sys.stderr)
        
        if status == 'completed':
            break
        elif status in ['failed', 'cancelled', 'expired']:
            print(f"Error: Assistant run {status}", file=sys.stderr)
            return None
        
        time.sleep(2)  # Check every 2 seconds
    
    # Get the response
    print(f"Getting assistant response...", file=sys.stderr)
    messages = client.beta.threads.messages.list(
        thread_id=thread.id,
        order='desc',
        limit=1
    )
    
    if messages.data:
        message = messages.data[0]
        if message.content:
            # Extract text from message content
            response_text = ""
            for content_block in message.content:
                if content_block.type == 'text':
                    response_text += content_block.text.value
            
            return response_text
    
    return None


def main():
    parser = argparse.ArgumentParser(description='Get AI analysis from OpenAI Assistant')
    parser.add_argument('--assistant-id', required=True,
                       help='OpenAI Assistant ID')
    parser.add_argument('--api-key', required=True,
                       help='OpenAI API Key')
    parser.add_argument('--questions-file', default='questions.txt',
                       help='File containing questions (default: questions.txt)')
    parser.add_argument('--calendar-json', default='forex_calendar_usd.json',
                       help='Calendar JSON file for context (default: forex_calendar_usd.json)')
    parser.add_argument('--output', default='ai_analysis.json',
                       help='Output JSON file (default: ai_analysis.json)')
    
    args = parser.parse_args()
    
    try:
        # Initialize OpenAI client
        print("Initializing OpenAI client...", file=sys.stderr)
        client = OpenAI(api_key=args.api_key)
        
        # Load questions
        print(f"Loading questions from: {args.questions_file}", file=sys.stderr)
        questions = load_questions(args.questions_file)
        
        if not questions:
            print("Error: No questions found in file", file=sys.stderr)
            sys.exit(1)
        
        print(f"Found {len(questions)} question(s)", file=sys.stderr)
        
        # Load calendar data for context
        calendar_data = load_calendar_data(args.calendar_json)
        if calendar_data:
            event_count = calendar_data.get('event_count', 0)
            print(f"Loaded calendar context: {event_count} events", file=sys.stderr)
        
        # Ask each question
        responses = []
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"Question {i}/{len(questions)}:", file=sys.stderr)
            print(f"{question[:80]}...", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            
            response = ask_assistant(
                client,
                args.assistant_id,
                question,
                calendar_context=calendar_data
            )
            
            if response:
                print(f"✅ Got response ({len(response)} characters)", file=sys.stderr)
                responses.append({
                    'question': question,
                    'response': response
                })
            else:
                print(f"❌ Failed to get response", file=sys.stderr)
                responses.append({
                    'question': question,
                    'response': 'Error: Failed to get response from assistant'
                })
        
        # Save output
        output_data = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'assistant_id': args.assistant_id,
            'question_count': len(questions),
            'responses': responses
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✅ SUCCESS! Saved to: {args.output}", file=sys.stderr)
        print(f"📊 Questions answered: {len(responses)}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        
        # Also print to stdout
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

