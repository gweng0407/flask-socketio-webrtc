window.onload = function () {
  var form = document.getElementById("uploadForm");
  var fileInput = document.getElementById("fileInput");
  var statusElement = document.getElementById("status");

  form.addEventListener("submit", function (event) {
    event.preventDefault(); // 기본 폼 제출을 막습니다.

    if (fileInput.files.length > 0) {
      var formData = new FormData();
      // 여러 파일을 처리하기 위해 formData에 파일들을 추가합니다.
      for (var i = 0; i < fileInput.files.length; i++) {
        formData.append("files", fileInput.files[i]);
      }

      var xhr = new XMLHttpRequest();
      xhr.open("POST", "http://localhost:5000/upload", true);
      xhr.onload = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
          statusElement.textContent = "File uploaded successfully";
          console.log(xhr.responseText);
        } else {
          statusElement.textContent = "Error uploading file";
          console.error("Error uploading file:", xhr.statusText);
        }
      };
      xhr.send(formData);
    } else {
      statusElement.textContent = "No file selected.";
    }
  });
};
