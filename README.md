# Dipping Bird

![Dipping Bird](dippingbird.gif)

Fully-automated* coding for Aider (currently couched with asterisks)

- All entry is done in the background, you can keep your mouse and keyboard to yourself.
- Assumes Windows environment for now (Win 10 pro tested)
- Claude-3.5-sonnet recommended, only one that stays consistent long enough
  - but Aider supports local models too
- USE AT YOUR OWN RISK

```
# install aider: https://aider.chat/

# create your project repo
# manually git init, Aider wont do it right afaik
git init
# copy /template folder into it and adjust/clean up GOALS.txt, ADVICE.txt, MODE.txt, STATUS.txt as needed (INSTRUCTIONS.txt can stay as is).  ADVICE.txt is your ongoing human feedback notes on the project

python -m aider --max-chat-history-tokens 100000 --no-gitignore --attribute-commit-message-author --sonnet

# add your files
/add ADVICE.txt
  GOALS.txt
  INSTRUCTIONS.txt
  README.md
  main.py
  requirements.txt
  STATUS.txt
  MODE.txt
```

Then in a separate terminal, run:

```
python dippingbird.py
```


# TODO

- [ ] get it to recursively define new module folders with their own fractal repeat of this template, so each module can be worked on independently and fit context restrictions (these do way better on smaller projects)
- [ ] have it setup unit tests in a procedural way
- [ ] have it setup inspection tests for the human user to peruse asynchronously and checkpoint progress (e.g. just browse the folder, run program, provide feedback, and Aider just adjusts to your feedback)
- [ ] get this more rigorous, minimal and tested lol - this was entirely just naive first-pass that worked