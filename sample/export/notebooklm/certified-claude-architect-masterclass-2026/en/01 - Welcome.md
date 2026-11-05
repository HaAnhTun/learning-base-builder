# Chapter 1: Welcome

## 1. Welcome to the Course

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · Lesson 1/136 · en_US · auto caption

**[00:00]** Welcome to the Claude Certified Architect Foundations course. I'm glad you're here. Before we start, I want to cover what the exam is, who it's for, and how to get the most out of this course. The exam is 60 questions in two hours, and you need a scaled score of 720 out of 1,000. It's a proctored exam online or at a test center, and the fee is $125 at the time of this recording. The content spans five domains.

**[00:26]** Agentic architectures and orchestration is the heaviest at 27%, then Claude code configuration and prompt engineering at 20% each, tool design and MCP integration at 18%, and context management and reliability at 15%, which in my opinion, is the most important domain. Anthropic recommends around six months of hands-on work with the Claude APIs, the agent SDK, Claude code, and MCP before you sit for this exam. One more thing before the lessons start because it changes how you move through the course. This program comes with a custom study pack. It's far more than a simple handout. There's a study companion that condenses the whole course into one document, a 30-day study plan that names the exact lectures to watch each day to be certified in a month, and three free mini-exam assessments at 30 questions each, all with full question and answer explanations.

**[01:21]** It also has a key terms glossary, printable flashcards, and every slide deck from this course for you to use. It doesn't cost a thing and it stays up to date. The last video in this course shows you exactly how to get it. It's free and it takes less than a minute to download. I'd go get it before starting the lessons because the study pack is what turns this course into a concrete path to success on exam day. In fact, let's quickly walk through how to download the resources.

**[01:51]** First, scroll all the way to the last lesson of the course and click on the Resources button. You'll need to scroll down a little bit more, then click the provided link. Once on the site, enter your information, then verify your account and it will redirect you to all the available resources. Look, people have different learning styles. Some really like using the slide decks and the study plan, along with the other resources. If that's you, pause here and go get them.

**[02:18]** If you're the type that doesn't need all that extra stuff, don't worry about it. Thousands of students have passed using only the video materials. That's actually how I like to learn. Now that you know about the study pack, we should talk about who this course is for because I'd rather you find out now than three lessons in. This course assumes you already use Cloud for real work. I don't cover setup and I don't walk through configuration.

**[02:43]** I also don't run code on screen. When I mention an example, I'm assuming you could go rebuild it on your own in your environment without me talking you through it. If that isn't where you are yet, that's completely fine. But this isn't your starting point. Go find a more foundational course and get some hands-on hours first. This course will be here when you're ready and you'll get far more out of it after doing that.

**[03:08]** Here's something that surprises people. This credential is valid for 12 months and then it expires. That isn't a catch. It's an honest response to a moving target. Cloud changes fast and a credential that stayed valid for five years would end up certifying that you knew a version of old Cloud that isn't valid anymore. So Anthropic keeps it current instead.

**[03:30]** When your renewal window opens, you renew what changed since you last certified. And it's completely free and non-proctored. The assessment is on the Anthropic Partner Academy website. There's no fee when you renew on time. What that buys you is a current tense statement that you know today's Cloud. And that you're an expert in Cloud as it stands in the current tense.

**[03:53]** There are two ways through this course, depending on where you are. If you're preparing for the first time, watch the lessons in order. They build on each other. So resist the urge to skip ahead on your first pass. Then work through the practice exams until you're scoring comfortably above that passing line of 720. If you're coming back to renew, you don't need to rewatch everything.

**[04:15]** Start with what changed. Watch the updated lessons and run fresh practice questions to confirm your judgment still tracks. Either way, the practice exams are your calibration tool. And there are plenty of them right here, all in one platform. Your access includes every update. So what you come back to is always current.

**[04:36]** One last piece of advice, and it's the one that pays off every renewal cycle. Learn the patterns, not the signatures. Names change, parameters change, and limits change. The reasoning behind a good design decision is durable. And that reasoning is what the exam is actually testing. When something is stable, I'll tell you.

**[04:55]** And when something is volatile, I'll tell you that too. So you know where your study time is worth spending. All right, that's enough talk. Let's get into the content.

## 2. Quick Conversation About the Course

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · Lesson 2/136 · en_US · auto caption

**[00:00]** Before we dive into the course, I want to explain a few things so you get the most out of this course. Take some time to listen to these. They might save you some headache. First, I want to be clear that this is a certification preparation course. Every lesson is built against the official exam blueprint. This exam is concept and scenario driven, and that's exactly how I teach these lessons.

**[00:22]** This is not a code along, and it's not a project build. If you're looking for a hands-on lab series, this is not it. What you will get is the mental models and the judgment the exam actually tests in the least amount of time possible. We didn't fill this course with a bunch of demos and industry examples, and that's on purpose. Ladies and gentlemen, AI is a race, and we want you to get certified as quickly as possible. So there's no filler, just what you need for exam day.

**[00:52]** Secondly, this course is made for people at varying experience levels. The most common feedback I hear is that the course either moves too fast or seems repetitive at times. Both are true, but they're usually about background, not the material itself. You see, most people watching this have five or more years of professional experience, but from different angles. Maybe you're a project manager, and the planning sections feel like old news, or maybe you've been writing code for years, and some of the methodology feels repetitive. I just ask for a little patience with that.

**[01:23]** Imagine yourself in a room with a big, diverse group of people with varying backgrounds. That's who this course is built for, and we worked hard to make it approachable and useful for all of you. This course will fill your knowledge gaps and have you prepared for exam day, but the cost is that you might hear one or two things that you already knew coming in. A quick note on the slide decks. We do use shorthand phrasing on the slides. They're meant as a visual anchor.

**[01:51]** I don't read from the slides either, since they're just an overview of the content. That's intentional. The slide anchors the idea, and my narration explains the idea. Focus on what I'm explaining, and let the slide be your visual reference, not a script to read along with. If you do like reading along, use the closed caption feature, and you'll get the best of both worlds. Another one that won't surprise you, I'm not perfect.

**[02:18]** Sometimes I make a mistake on a slide, or you'll hit a practice question where you're convinced the answer is wrong. Either way, help me and help your fellow students out. Send me a direct message and tell me what you saw. I'll verify it against the official documentation, and the confirmed fixes will go back into the course for everyone to benefit from. Another quick note. Check the resources section of this lecture before you go any further.

**[02:44]** We attach a lot of resources, either to this lesson or to the final lesson of the course. This course ships with multiple downloads, a condensed review of the entire course that we call the study companion, a key terms cram sheet for quick reference, a 30-day study plan to structure your prep, and more. If you don't see what you're looking for attached to this lesson, check the final lesson of the course to find those resources. And one final thing about pace. Some people tell me that I talk too slowly. Others tell me I move too fast.

**[03:15]** Both are easy to fix using the speed controls in the video player. Just set the pace where it's comfortable for you. Okay, that's it on this stuff. Let's get started on the actual course content. I'll see you in the first lesson.
