# WinjaCTF c0c0n 2020

### Sourcery

``` http://159.89.163.92:83/yBXjJxBqyGbalyG7kJQWXvMdzY5YE/ ```

Gives a text,
> /TODO: Update code

<img src="./img/chall.png" alt="Challange-img" width="500"/>

<img src="./img/img1.png" alt="Challange-img" width="750"/>

### Approach

Look for source code, and we found something

<img src="./img/img2.png" alt="Challange-img" width="1000"/>

Git Repo has 4K+ commits

<img src="./img/img3.png" alt="Challange-img" width="500"/>

clone the repo to local machine and checked random commit, and it seems like files are randomly added and deleted.

<img src="./img/img5.png" alt="Challange-img" width="500"/>

** Bash onliner **

``` bash
git log | grep commit | cut -d ' ' -f2 | xargs git show | grep -i flag --color
```

<img src="./img/img4.png" alt="Challange-img" width="500"/>
