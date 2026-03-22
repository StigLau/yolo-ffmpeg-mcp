# Architecture

The project follows a modular architecture, with each module responsible for a specific set of functionalities. The main components of the architecture are:

*   **`server.py`**: This is the main entry point of the application. It uses the `FastMCP` framework to expose a set of tools that can be called remotely. The server is responsible for handling incoming requests, calling the appropriate tools, and returning the results.

*   **`ffmpeg_wrapper.py`**: This module provides a safe and convenient way to interact with the `ffmpeg` command-line tool. It defines a set of allowed operations and their corresponding command-line arguments, which helps to prevent command injection vulnerabilities. It also includes "smart" logic for some operations, like automatically handling different video resolutions when concatenating videos.

*   **`file_manager.py`**: This module is responsible for managing files and their IDs. It provides a secure way to access files by using randomly generated IDs instead of direct file paths. This helps to prevent unauthorized access to the filesystem. The `FileManager` also includes a caching mechanism for file properties, which helps to improve performance.

*   **`content_analyzer.py`**: This module uses `PySceneDetect` and `OpenCV` to analyze video content. It can detect scene changes, identify objects within scenes, and provide a summary of the video's content. This information can then be used to make "intelligent" editing decisions, such as automatically suggesting the best scenes to include in a highlight reel.

*   **`komposition_processor.py`**: This module is responsible for creating beat-synchronized music videos from a `komposition` JSON file. The `komposition` file defines the structure of the music video, including the video clips to use, their timing, and the background music.

*   **Other modules**: The project also includes a number of other modules that provide additional functionalities, such as speech detection, transition effects, and enhanced speech analysis.

The project is designed to be highly extensible, and new modules and functionalities can be easily added. The use of the `FastMCP` framework makes it easy to expose new tools and make them available to remote clients.
