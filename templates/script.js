document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search");
  const imageGrid = document.getElementById("image-grid");
  const downloadButton = document.getElementById("downloadButton");
  const selectedImages = [];

  function fetchImages(query) {
      const apiUrl = `https://bing-image-search1.p.rapidapi.com/images/search?q=${query}`;

      fetch(apiUrl, {
          method: "GET",
          headers: {
            'X-RapidAPI-Key': '2f6bf114b8msh00bb3f1b317737dp1a2729jsna070df4af051',
            'X-RapidAPI-Host': 'bing-image-search1.p.rapidapi.com',

          }
      })
          .then((response) => response.json())
          .then((data) => {
              displayImages(data.value);
          })
          .catch((error) => {
              console.error("Error fetching images:", error);

          });
  }

  function displayImages(images) {
      imageGrid.innerHTML = "";

      images.forEach((image) => {
          const imgElement = document.createElement("img");
          imgElement.src = image.contentUrl;
          imgElement.classList.add("img-thumbnail", "mx-2", "my-2","card");

          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.classList.add("image-checkbox");
          checkbox.value = image.contentUrl;

          checkbox.addEventListener("change", function () {
              if (checkbox.checked) {
                  selectedImages.push(image.contentUrl);
              } else {
                  selectedImages.splice(selectedImages.indexOf(image.contentUrl), 1);
              }
              updateDownloadButtonState();
          });

          const col = document.createElement("div");
          col.classList.add("col-md-4", "col-sm-6");
          col.appendChild(checkbox);
          col.appendChild(imgElement);

          imageGrid.appendChild(col);
      });
  }

  console.log(selectedImages)
  function updateDownloadButtonState() {
      if (selectedImages.length > 0) {
          downloadButton.disabled = false;
      } else {
          downloadButton.disabled = true;
      }
  }

  searchInput.addEventListener("input", function () {
      const query = searchInput.value.trim();
      fetchImages(query);
  });

  downloadButton.addEventListener("click", function () {
      if (selectedImages.length > 0) {
          const zip = new JSZip();
          const imgFolder = zip.folder("images");
          console.log(selectedImages)
          selectedImages.forEach((imageUrl, index) => {
            console.log(imageUrl)
              fetch(imageUrl)
                  .then((response) => response.blob())
                  .then((blob) => {
                      imgFolder.file(`image${index + 1}.jpg`, blob, {base64: true});
                      if (index === selectedImages.length - 1) {

                          imgFolder.generateAsync({ type: "blob" }).then((content) => {
                              const zipFileName = "selected_images.zip";
                              saveAs(content, zipFileName);
                          });
                      }
                  });
          });
      }
  });


  fetchImages("cow");
});