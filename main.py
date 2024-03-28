# Copyright (C) 2023, Roman V. M.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
WikiFlix video plugin that is compatible with Kodi 20.x "Nexus" and above
"""
import json
import sys
import urllib.request
from urllib.parse import parse_qsl, urlencode

import xbmcgui
import xbmcplugin

# import os
# from xbmcaddon import Addon
# from xbmcvfs import translatePath

# Get the plugin url in plugin:// notation.
URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])
# Get addon base path
# ADDON_PATH = translatePath(Addon().getAddonInfo("path"))


def movie_conversion(movie):
    thumbnail_width = "640"  # px

    if "available" not in movie or movie["available"] != "1":
        return None

    movie_url = None
    for file in movie["files"]:
        if file["is_trailer"] != 0:
            continue
        if file["property"] == 10:
            movie_url = (
                "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/"
                + file["key"].replace(" ", "_")
            )
        # if file["property"] == 724: # Does not work like this
        #     movie_url = "https://archive.org/embed/"+file["key"]
    if movie_url is None:
        # No streamable video found
        return None
    image_url = None
    if movie["image"] is not None:
        image_url = (
            "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/"
            + movie["image"].replace(" ", "_")
            + "&width="
            + thumbnail_width
        )
    year = None
    if movie["year"] is not None:
        year = int(movie["year"])
    plot = None
    if movie["minutes"] is not None:
        plot = f"{movie['minutes']} min"
    o = {
        "title": movie["title"],
        "url": movie_url,
        "poster": image_url,
        "plot": plot,
        "year": year,
        "sites": int(movie["sites"]),
    }
    return o


sections = []
had_section_q = []
sections_url = "https://wikiflix.toolforge.org/all.json"
# trunk-ignore(bandit/B310)
with urllib.request.urlopen(sections_url) as url:
    data = json.load(url)
    for section in data["sections"]:
        o = section
        if "title" not in o or o["title"] is None:
            continue
        if "q" not in o or o["q"] in had_section_q:
            continue
        had_section_q.append(o["q"])
        o["genre"] = o["title"]
        o["movies"] = []
        o["icon"] = None
        o["fanart"] = None
        for movie in o["entries"]:
            m = movie_conversion(movie)
            if m is not None:
                o["movies"].append(m)
        if len(o["movies"]) > 0:
            sections.append(o)


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return "{}?{}".format(URL, urlencode(kwargs))


def get_genres():
    """
    Get the list of video genres

    Here you can insert some code that retrieves
    the list of video sections (in this case movie genres) from some site or API.

    :return: The list of video genres
    :rtype: list
    """
    return sections


def get_videos(genre_index):
    """
    Get the list of videofiles/streams.

    Here you can insert some code that retrieves
    the list of video streams in the given section from some site or API.

    :param genre_index: genre index
    :type genre_index: int
    :return: the list of videos in the category
    :rtype: list
    """
    return sections[genre_index]


def list_genres():
    """
    Create the list of movie genres in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(HANDLE, "Public Domain Movies")
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(HANDLE, "movies")
    # Get movie genres
    genres = get_genres()
    # Iterate through genres
    for index, genre_info in enumerate(genres):
        # Create a list item with a text label.
        list_item = xbmcgui.ListItem(label=genre_info["genre"])
        # Set images for the list item.
        list_item.setArt({"icon": genre_info["icon"], "fanart": genre_info["fanart"]})
        # Set additional info for the list item using its InfoTag.
        # InfoTag allows to set various information for an item.
        # For available properties and methods see the following link:
        # https://codedocs.xyz/xbmc/xbmc/classXBMCAddon_1_1xbmc_1_1InfoTagVideo.html
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType("video")
        info_tag.setTitle(genre_info["genre"])
        info_tag.setGenres([genre_info["genre"]])
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&genre_index=0
        url = get_url(action="listing", genre_index=index)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    # Add sort methods for the virtual folder items
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)


def list_videos(genre_index):
    """
    Create the list of playable videos in the Kodi interface.

    :param genre_index: the index of genre in the list of movie genres
    :type genre_index: int
    """
    genre_info = get_videos(genre_index)
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(HANDLE, genre_info["genre"])
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(HANDLE, "movies")
    # Get the list of videos in the category.
    videos = genre_info["movies"]
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label
        list_item = xbmcgui.ListItem(label=video["title"])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use only poster for simplicity's sake.
        # In a real-life plugin you may need to set multiple image types.
        if video["poster"] is not None:
            list_item.setArt({"poster": video["poster"]})
        # Set additional info for the list item via InfoTag.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType("movie")
        info_tag.setTitle(video["title"])
        info_tag.setGenres([genre_info["genre"]])
        if video["plot"] is not None:
            info_tag.setPlot(video["plot"])
        if video["year"] is not None:
            info_tag.setYear(video["year"])
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty("IsPlayable", "true")
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=https%3A%2F%2Fia600702.us.archive.org%2F3%2Fitems%2Firon_mask%2Firon_mask_512kb.mp4
        url = get_url(action="play", video=video["url"])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    # Add sort methods for the virtual folder items
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    # offscreen=True means that the list item is not meant for displaying,
    # only to pass info to the Kodi player

    play_item = xbmcgui.ListItem(offscreen=True)
    play_item.setPath(path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if not params:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_genres()
    elif params["action"] == "listing":
        # Display the list of videos in a provided category.
        list_videos(int(params["genre_index"]))
    elif params["action"] == "play":
        # Play a video from a provided URL.
        play_video(params["video"])
    else:
        # If the provided paramstring does not contain a supported action
        # we raise an exception. This helps to catch coding errors,
        # e.g. typos in action names.
        raise ValueError(f"Invalid paramstring: {paramstring}!")


if __name__ == "__main__":
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
