// api
const api = {
  endpoints: {
    settings: "/settings/",
    galleries: "/galleries/",
    deleteImage: '/delete-image/',
    images(gallery, show_mode) {
      return `/galleries/${gallery}/images/?show_mode=${show_mode}`;
    },
    markImage(gallery, img_name) {
      return `/galleries/${gallery}/images/${img_name}/mark`;
      
    }
  },
  getGalleries () {
    return fetch(this.endpoints.galleries)
    .then(response => response.json());
  },
  getSettings () {
    return fetch(this.endpoints.settings)
    .then(response => response.json());
  },
  saveSettings (settings) {
    return fetch(this.endpoints.settings, {
      method: 'POST',
      body: JSON.stringify(settings)
    });
  },
  getImages(gallery, show_mode) {
    const url = this.endpoints.images(gallery, show_mode);
    return fetch(url)
      .then(response => response.json())
      .catch(err => alert(err));
  },
  markImage(gallery, img_name) {
    return   fetch(this.endpoints.markImage(gallery, img_name), 
      {
        method: "POST"
      }
    )
        .then(response => response.json());
  }, 
  deleteImage(gallery, url) {
    return fetch(this.endpoints.deleteImage + gallery + "/" + url,
      {
        method: "POST"
      });
  }
};

// app
const app = {
  api,
  data: {
    galleries: [],
    settings: {},
    currentImage: "",
    images: []
  },
  getGalleries() {
    return this.api.getGalleries()
    .then(data => {
      this.data.galleries = data;
      return data;
    });
  },
  getImages() {
    const settings = this.data.settings;
    
    return this.api.getImages(settings.selected_gallery, settings.show_mode)
    .then(data => {
      
      this.data.images = data;
      return data;
    })
   .catch(error => alert(error));
  },
  getSettings() {
    return this.api.getSettings()
    .then(data => {
      console.log(data);
      this.data.settings = data;
      return data;
    });
  },
  saveSettings(settings) {
    return this.api.saveSettings(settings)
    .then(response => {
      if (response.ok) {
        this.data.settings = settings;
        return this.getImages();
      }
    })
    .then(() => true);
  },
  markImage() {
      const settings = this.data.settings;
      const currImage = this.data.currentImage;
      
      this.api.markImage(
          settings.selected_gallery,
          currImage.name
      ).then(img_info => {
          if (settings.show_mode == "unmarked") {
              this.deleteImageFromImages(currImage);
              this.redraw();
          } else {
              const images = this.data.images;
              const idx = images.indexOf(currImage);              images[idx] = img_info;
              this.data.currentImage = img_info;
              this.drawImage(this.data.currentImage);
          }
      });
  },
  deleteImageFromImages(image) {
      const images = this.data.images;
      const idx = images.indexOf(image);
      if(idx >= 0){
          images.splice(idx,1);
      }    
  },
  deleteImage() {
    this.api.deleteImage(this.data.settings.selected_gallery,
      this.data.currentImage.name)
    .then(response => {
      if (response.ok) {
          this.deleteImageFromImages(this.data.currentImage); 
        this.redraw();
      }
    });
  },
  randomImage() {
    const images = this.data.images;
    
    return images[Math.floor(Math.random() * images.length)];
  },
  showImage(url) {
    const image = document.getElementById("image");
    image.src = url;
  },
  drawErrorContainer(message) {
    const imageContainer = document.getElementById("imageContainer");
    imageContainer.innerHTML = "";

    const msgElement = document.createElement("p");
    msgElement.innerHTML = message;
    msgElement.className = "error-message";
    imageContainer.append(msgElement);
  },
  drawImage(image) {
      const imgNameDiv = document.getElementById("imageName");
    imgNameDiv.innerHTML = image.name;

    this.showImage(image.url);
  },
  redraw() {
    const image = this.randomImage();
    //alert(image);
    this.data.currentImage = image;
    this.drawImage(this.data.currentImage);
  },
  start() {
    this.getSettings()
      .then(settings => {
        if(settings.show_mode && settings.selected_gallery) {
        
          return this.getImages();
        
        } else {
          return Promise.reject(
            new Error("pick settings in sidenav"));
        }
        
      })
      .then(images => this.redraw())
      .catch(err => this.drawErrorContainer(err.message));
      
  }
};

// side navigation
const sidenavOpen = document.getElementById("sidenavOpen");
const sidenavClose = document.getElementById("sidenavClose");
const sidenav = document.getElementById("sidenav");
const saveButton = document.getElementById("btnSave");

sidenavOpen.addEventListener("click", () => {
  sidenav.classList.add("sidenav-open");


  const gallsContainer = document.getElementsByClassName("galleries-container")[0];
  gallsContainer.innerHTML = "";

  Promise.all([app.getGalleries(), app.getSettings()])
  .then(results => {
    // draw galleries
    const galls = results[0];
    const settings = results[1];

    const selected_gallery = settings && settings.selected_gallery;
    const show_mode = settings && settings.show_mode;
    document.getElementById("showMode").value = show_mode;

    galls.map((gallery) => {
      const elem = document.createElement("a");
      elem.innerHTML = gallery.title;
      elem.dataset.id = gallery.slug;
      elem.href = "javascript:void(0);";
      if (gallery.slug == selected_gallery) {
        elem.classList.add("selected");
        elem.dataset.active = "true";
      }

      elem.onclick = () => {
        if (elem.classList.contains("selected")) {
          return;
        }
        const prevSelected =
        document.querySelector(".galleries-container a.selected");
        if (prevSelected) {
          prevSelected.classList.remove("selected");
        }
        elem.classList.add("selected");
      };
      
      gallsContainer.append(elem);
    });
  });

});

function closeSidenav() {
  sidenav.classList.remove("sidenav-open");
}

sidenavClose.addEventListener("click", closeSidenav);

saveButton.addEventListener("click", () => {
  const settings = {
    show_mode: document.getElementById("showMode").value,
    selected_gallery: document.querySelector(".galleries-container a.selected").dataset.id
  };
  
  app.saveSettings(settings)
  .catch(error => console.log(error.message))
  .finally(() => {
    closeSidenav();
    app.redraw();
  });
});

function ImageButtons(app) {
  this.app = app
  
  this.randomButton = document.getElementById("random");
  this.randomButton.addEventListener('click', 
    () => this.app.redraw());
  
  
  this.deleteButton = document.getElementById("delete");
  this.deleteButton.addEventListener("click", () => this.app.deleteImage());
  
  this.markButton = document.getElementById("mark");
  this.markButton.addEventListener("click", 
    () => {
      if (!this.app.data.currentImage.marked) {
      
        this.app.markImage();
      } 
    });
    
}


panel = new ImageButtons(app);

app.start();