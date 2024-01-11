$("#local_vid").draggable({
  containment: "body",
  zIndex: 10000,
  // set start position at bottom right
  start: function (event, ui) {
    ui.position.left = $(window).width() - ui.helper.width();
    ui.position.top = $(window).height() - ui.helper.height();
  },
});

function checkVideoLayout() {
  const video_grid = document.getElementById("video_grid");
  const videos = video_grid.querySelectorAll("video");
  const video_count = videos.length;

  if (video_count === 0) {
    // Handle the case when there are no videos
  } else {
    // Calculate dynamic layout based on the number of videos
    const rows = Math.ceil(Math.sqrt(video_count));
    const cols = Math.ceil(video_count / rows);

    videos.forEach((video, index) => {
      video.style.width = `${100 / cols}%`;
      video.style.height = `${100 / rows}vh`;
      video.style.objectFit = "cover";
    });
  }
}

// Example: Trigger the layout check when the window is resized
$(window).resize(checkVideoLayout);

// Example: Call the layout check function initially
checkVideoLayout();
