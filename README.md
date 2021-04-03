# Manganelo Downloader
A multi-threaded scraper used to fetch and download images (manga pages) from manganelo.tv

## Why?
This was originally created so I could read my manga offline, and to avoid having to use the sometimes clunky website.

## How?
To run, either build the executable file using `setup.py`, or run the following commands:
	- `pip install -r requirements.txt`
	- `python manga-dl.py -h`

## Options
All options and arguments are described with the -h command, but are listed here for convenience.
For quick download, you can run the command:
`manga-dl [URL for manga without the chapter number (https://manganelo.tv/chapter/kono_subarashii_sekai_ni_shukufuku_o/chapter_)]`

Full command list:
	- -h : Shows the help command
	- -w / --workers [int]: Set the worker count (How many threads should we create?)
	- -c / --chapters[int]: Amount of chapters to download
	- -n / --manganame: Name of the manga, used for folder creation
	- --cdnregex [REGEX]: Custom regex to match image urls against

## How to view
Once manga-dl has finished downloading your mangas, it will have created a folder called `Unnamed Manga` if you have not specified a --manganame. Inside will be each chapter folder and a `chapter.html`. Opening this will allow you to view the manga chapter by chapter with links to each next chapter.


## Troubleshooting
This has only been tested and made for Windows. Since this program uses curses it is dependant on windows-curses for Windows operation. You may try removing this dependancy from `requirements.txt` and instead installing curses for Linux. YMMV
