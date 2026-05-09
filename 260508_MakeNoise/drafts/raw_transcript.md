# Raw Transcript

**Source**: https://www.youtube.com/watch?v=gSAGc_-cWrs
**Title**: Make Noise: Soundhack Plexiphon - Superbooth 2026
**Channel**: sonicstate
**Language**: English
**Duration**: 8:33
**Subtitles**: YouTube auto-generated (en-orig)

---

**Interviewer (Matt)**: Hello Walker. Hello Matt. Welcome back.

**Walker (Make Noise)**: Thank you.

**Matt**: Superbooth 2026, this is my first video of day two. So I had to get here because I read a little bit about this and I saw your video. This is the new Plexiphon, right? That's right. So what is it?

**Walker**: It's the SoundHack Plexiphon. It is a new stereo spatial texturizer module that we developed in conjunction with Tom Erb. We've of course worked with him on many projects before — from the Morphagene to Spectraphon, Mimeophon and plenty of others. So this module is encoded from scratch on a brand new idea by Tom on our latest digital hardware, and it is taking the idea of "Plexus" which gives it its name — that is the Latin root for "weave" — and what it's doing is weaving some sound together through a number of different feedback paths and what you might say delay taps. The Plexus control being the key control, it will determine the overall number of feedback paths and delay taps and how complex the relationship between those is. So when we have Plexus turned all the way down as it is now, the module operates as if it's kind of like a reverb because many of the paths are all very tightly interwoven to create this sense of echoing space, and the size control here will operate like the size control of a reverb. Now as we turn the Plexus up more and more, we'll start to hear the individual taps beginning to stick out in the mix a little more.

**Matt**: Yeah. The overall relationship between them becomes less complex. There become fewer and fewer of them and it becomes more like a multi-tap echo.

**Walker**: Yeah, and the size is now akin to a rate control on an echo module. And we can always move very smoothly from one extreme to the other of Plexus. And a lot of the development time on this module was just ensuring that we can do all this very smoothly. Very smooth switch from reverb to delay. Very smooth modulation of size. Smooth modulation of timbre parameters like color.

**Matt**: You're just sending that an envelope there from Maths?

**Walker**: That's right. Just a very simple cycling function there that will determine the timbre at any given moment.

**Matt**: That's great.

**Walker**: The Diffuse and Color are our timbre parameters, and then we also have the Couple and Skew, which are stereo operations. We'll go into those in more detail when we get closer to release, but essentially Couple is determining how the left and right channels are interacting sound-wise, and Skew giving some other options for interacting with the left and right channels control-wise.

**Matt**: I'm trying to get an idea of the signal path. It sounds to me like everything's kind of working together. It's not necessarily a linear signal path throughout the module.

**Walker**: It seems like you've got feedback and elements working on each other in different ways. These parameters are highly interrelated to each other because we're always working on a different number of delay paths — with Plexus changing the number of delay paths, it's also changing the relation between them. And the controls are all operating on, at any given time, a number of different paths in different ways. So the controls are really highly interrelated, and developing this module was a lot about finding the exact relations between them so that they could all interact without anything causing the whole system to explode — which was happening a lot during development. But I feel like we've fine-tuned it very nicely and it's very playable. It's modeless. You can reach every single extreme of parameter from any place at any time.

We also have the Send Gate input. This is one last little trick I'd want to show you — if we hold that low, it just doesn't send anything through to the Plexus. But if I send a gate in, then whatever's coming through at that moment that the gate is high will be sent in and then continue to echo out through the paths. And then when the gate goes low again, you can still hear it echoing out, but new things are not brought in. So this can be really useful if you want to send a gate sequence — say from the even output of my GTE here — we could send just individual notes of a sequence through, so that it's not just echoing everything, but you're getting some kind of pointillist echoes that are helping it work with the shape and contour of your sequence and add some depth to specific places.

**Matt**: It's great. I mean, the final output of it isn't a typical delay or reverb sound. It feels like it's a very kind of blurred world that they're both situating themselves into. It's quite a hard one to describe, really. But it sounds absolutely lovely. As I like to call things, they're really vibey.

**Walker**: Very much so. And it can give you really nice kind of beautiful textures to overlay or have things sit into, or you can get wild with modulation and turn it into kind of its own entire voice instrument in itself in a lot of ways.

**Matt**: Can you show us like a really big decay, how extreme can this go if we wanted to go wild with it? Oh, nice. Listen to that. Wow. Awesome. Brilliant. So, when can we expect to see this available?

**Walker**: We'll be shipping this in early June at a MSRP of $469 USD.

**Matt**: Amazing. Great stuff. As always, Make Noise, keep making noise and making these wonderful products for us. Thank you.

**Walker**: Thanks so much for coming by, Matt. Cheers, man.
