# Q1 Test Calls & Transcripts

**Instructions for the Candidate:**
The assessment requires: *"Record at least three test calls and submit transcripts and results. Required Test Coverage: Cooperative customer; objection; incomplete or conflicting details; out-of-scope question; human-assistance request."*

### 📥 How to get your Audio and Transcripts
Since we set `"recordingEnabled": True` in the agent config, **Vapi records all your calls automatically**.
1. Run the Voice Bot from the Web UI (`http://localhost:8080`).
2. Do the 3 test calls using the scripts below.
3. Log into your [Vapi Dashboard](https://dashboard.vapi.ai) and go to the **Calls** tab.
4. Download the audio files and copy the transcripts.
5. Drop the audio files into this `test_evidence/` folder and paste the transcripts below.

---

### 🎭 Call Scripts for you to read

#### Test Call 1 (Cooperative Customer)
**You:** "Hi, I'm interested in buying health insurance. What plans do you have?"
**Bot:** *(Explains plans)*
**You:** "I think the Individual Plan sounds good. How much does it cost?"
**Bot:** *(Explains pricing/process)*
**You:** "Great, let's schedule a callback so I can finalize it."

**Audio File:** 
**Transcript:**
> [
Health Shield RAG Agent
Hi, this is Alex from HealthShield. I saw you were looking into our health insurance plans. Do you have a quick minute to see if you qualify?
9:46:33 AM(+00:11.80)
User
Do you have?

9:46:38 AM(+00:16.58)

Health Shield RAG Agent
Yes, we have several health insurance plans available to see which ones you qualify for. Could you tell me if you are between the ages of 18 and 65?
9:46:49 AM(+00:27.70)
User
25.

9:46:53 AM(+00:31.57)

Health Shield RAG Agent
Perfect. That fits right in our range. Are you looking to cover just yourself?
9:46:59 AM(+00:37.68)

Health Shield RAG Agent
Or are you looking to include your family as well?
9:47:02 AM(+00:40.46)
User
Individual plans? Also? How much does it cost?

9:47:05 AM(+00:43.55)

ApiRequest-D861c2a5
Completed successfully
09:47

9:47:08 AM(+00:46.70)

Health Shield RAG Agent
Let me quickly check our policy documents for that.
9:47:11 AM(+00:49.62)
User
So whenever you are ready with that, just. Answer.

9:47:18 AM(+00:56.84)

ApiRequest-D861c2a5
Completed successfully
09:47

9:47:19 AM(+00:57.99)

Health Shield RAG Agent
Let me quickly check our policy documents for that.]

---

#### Test Call 2 (Objection & Conflicting Details)
**You:** "Hi, I was looking at your health insurance, but honestly, it's way too expensive compared to competitors." *(Objection)*
**Bot:** *(Handles objection gracefully)*
**You:** "Well, I might still be interested. I'm 25 years old... wait, no, I'm 55 years old." *(Conflicting details)*
**Bot:** *(Should ask to clarify age)*
**You:** "Sorry, I am 55. What are the rules for pre-existing diseases?"
**Bot:** *(Looks up Knowledge Base for PED rules)*

**Audio File:** `[Drop file here]`
**Transcript:**
> [


Health Shield RAG Agent
Hi, this is Alex from HealthShield. I saw you were looking into our health insurance plans.
10:19:04 AM(+00:11.90)

Health Shield RAG Agent
Do you have a quick minute to see if you qualify?
10:19:06 AM(+00:14.01)
User
Alex.

10:19:33 AM(+00:41.68)

Health Shield RAG Agent
I'm glad I reached you.
10:19:37 AM(+00:45.18)
User
Ander.

10:19:41 AM(+00:49.35)

Health Shield RAG Agent
To see if we have a plan that fits your needs. Could you tell me if you are looking for coverage.
10:19:42 AM(+00:49.76)

Health Shield RAG Agent
Hi Ander, nice to meet you. To see if we have the right plan for you, can I start by asking if you are between the ages of 18 and 65?
10:19:52 AM(+01:00.16)
User
Actually it was like your plans are too expensive compared to competitors.

10:19:59 AM(+01:07.19)

ApiRequest-2908df92
Completed successfully
10:20

10:20:00 AM(+01:08.35)

Health Shield RAG Agent
Let me quickly check our policy documents for that.
10:20:03 AM(+01:11.14)
User
Did you find. Any.

10:20:15 AM(+01:23.55)

Health Shield RAG Agent
I don't have the specific pricing comparison details right in front of me.
10:20:22 AM(+01:30.37)

Health Shield RAG Agent
But our senior agent can definitely walk you through our competitive rates and discounts during a callback.
10:20:28 AM(+01:35.98)

Health Shield RAG Agent
To see if we can get you qualified for those rates, are you currently between the ages of 18 and 65?
10:20:34 AM(+01:41.97)
User
Assignment 25.

10:20:36 AM(+01:44.37)

Health Shield RAG Agent
I'm here to help you with your health insurance needs today. To see if we can find a plan that fits your budget, are you currently between the ages of 18 and 65?
10:20:46 AM(+01:54.48)
User
Yes I'm 25.

10:20:49 AM(+01:57.38)

Health Shield RAG Agent
Great, thanks for confirming.
10:20:53 AM(+02:01.59)

Health Shield RAG Agent
Are you looking to cover just yourself or are you looking to include family members as well?
10:20:58 AM(+02:06.61)
User
I'm just looking to. Plan.

10:21:02 AM(+02:10.17)

Health Shield RAG Agent
Just yourself. Got it.
10:21:10 AM(+02:18.57)

Health Shield RAG Agent
Do you have any pre-existing medical conditions that we should be aware of?
10:21:15 AM(+02:23.11)
User
No no thank you I'm like ending the call.

10:21:19 AM(+02:27.35)

EndCall
Completed successfully
10:21
10:21:21 AM(+02:28.84)

Health Shield RAG Agent
]

---

#### Test Call 3 (Out-of-Scope & Human Assistance)
**You:** "Hi, I need help fixing the engine in my Toyota Corolla. Can you send a mechanic?" *(Out-of-scope question)*
**Bot:** *(Should state it cannot help with that instead of inventing an answer)*
**You:** "Oh, okay. Can I add my newborn baby to my health policy?"
**Bot:** *(Looks up Knowledge Base for newborn rules)*
**You:** "This is too confusing. I want to speak to a human manager right now." *(Human assistance request)*
**Bot:** *(Handles escalation / callback)*

**Audio File:** `[Drop file here]`
**Transcript:**
> [

Health Shield RAG Agent
Hi, this is Alex from HealthShield. I saw you were looking into our health insurance plans. Do you have a quick minute to see if you qualify?
10:28:06 AM(+00:12.54)
User
Hi, I am I need help fixing the engine in my Toyota Coroll. A. Can you send a mechanic?

10:28:12 AM(+00:19.06)

Health Shield RAG Agent
I'm sorry, but I can only assist with Health Shield health insurance plans. If you're interested in health insurance, I'd be happy to see if you qualify.
10:28:25 AM(+00:31.52)
User
Oh, okay. Can I add my new one baby to my health policy?

10:28:30 AM(+00:36.81)

Health Shield RAG Agent
Function call Default API.
10:28:35 AM(+00:42.09)

Health Shield RAG Agent
Request minus 66257881.
10:28:42 AM(+00:48.89)
User
Can I. Add a newborn baby to my health polic. Y?

10:28:49 AM(+00:56.27)

ApiRequest-66257a81
Completed successfully
10:28

10:28:53 AM(+01:00.34)

Health Shield RAG Agent
Let me quickly check our policy documents for that.
10:28:56 AM(+01:03.19)
User
Are you ready?

10:29:16 AM(+01:22.72)

Health Shield RAG Agent
Yes, I can check that for you.
10:29:20 AM(+01:27.27)

Health Shield RAG Agent
To make sure we find the right policy details, are you looking to cover just yourself and the baby?
10:29:26 AM(+01:32.61)

Health Shield RAG Agent
Or other family members as well?
10:29:27 AM(+01:34.29)
User
Just for. Being.

10:29:29 AM(+01:36.33)

Health Shield RAG Agent
Got it. And to make sure we find the right plan, how old are you?
10:29:36 AM(+01:42.77)
User
Too confusing? I want to speak to a human manager right now.

10:29:41 AM(+01:48.24)

Health Shield RAG Agent
I understand.
10:29:44 AM(+01:50.88)

Health Shield RAG Agent
I am transferring you to a human representative right now.
10:29:47 AM(+01:54.19)
User
Thank you. End the call.

10:29:49 AM(+01:56.23)

EndCall
Completed successfully
10:29
10:29:51 AM(+01:58.47)
Assistant ended the call]
