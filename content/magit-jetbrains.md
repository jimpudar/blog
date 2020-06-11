Title: Integrate Magit With JetBrains
Date: 2020-04-15
Category: Development
Tags: emacs, magit, jetbrains, ide, git
Slug: magit-jetbrains
Author: Jim Pudar
Summary: How to integrate Magit in a JetBrains workflow
Status: published

I'm a huge fan of [Magit](https://magit.vc/). I honestly can't imagine doing
software development without it. However, I've recently moved from Emacs to
JetBrains products like PyCharm, WebStorm, and IntelliJ to take advantage of
some of their more advanced features. In my opinion, Magit is light years
ahead of the JetBrains version control client.

I wanted a good way to integrate my existing Magit workflow into my new
JetBrains workflow. I started off with some hints from
[JetBrains](https://www.jetbrains.com/help/idea/using-emacs-as-an-external-editor.html#)
and some more from Atlassian's [Developer
Blog](https://www.jetbrains.com/help/idea/using-emacs-as-an-external-editor.html#)
and came up with something that works for me.

![Screenshot of External Tool dialog]({photo}screenshots/magit-external-tool-screenshot.png)

```text
Program:            /usr/local/bin/emacsclient
Arguments:          -n -e "(progn (x-focus-frame nil) (magit-status))"
Working directory:  $FileDir$
```

Ensure Emacs is always running (it already is, right?) and that you have
started a server. I make sure this happens by default by adding
`(server-start)` to my Emacs config file.

Now, you can call `emacsclient` to pass commands to your running server.

In this External Tool configuration, we are calling `(x-focus-frame nil)` to
bring your Emacs frame to the foreground. This works on macOS Catalina, but
you might need to try `(raise-frame)` if you are on a different OS.

Finally, calling `(magit-status)` will bring up the Magit status page.

Make sure the "Open console for tool output" is unchecked to avoid cluttering
your JetBrains workspace.

Finally, you can assign the External Tool to a keyboard shortcut or assign it
an abbreviation in Preferences > Keymap.

For more ideas, see [Invoking
`emacsclient`](https://www.gnu.org/software/emacs/manual/html_node/emacs/Invoking-emacsclient.html)
and [`emacsclient`
Options](https://www.gnu.org/software/emacs/manual/html_node/emacs/emacsclient-Options.html)
