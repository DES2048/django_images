import XWiper from "xwiper";
import api from "./api";
import Sidenav from "./components/sidenav.js";
import ImageDrawer from "./components/image-drawer.js";

// functions for comparsions
function compareValues(a, b) {
    if (a == b) {
      return 0;
    } else if (a < b) {
      return -1;
    } else {
      return 1;
    }
  }
  
  function invertComparsion(cmp_result) {
    if (cmp_result > 0) {
      return -1;
    } else if (cmp_result < 0) {
      return 1;
    } else {
      return 0;
    }
  }

// Application class
export default class App {
    constructor() {
      this.api = api;
      
      this.imageDrawer = new ImageDrawer();
      this.sidenav = new Sidenav(this);
  
      this.data = {
        galleries: [],
        settings: {},
        currentImage: "",
        images: [],
        currentImageIndex: -1,
      }

      this._setXWiper();
      this._setEventHandlers();
      this.start();
    }
    _setXWiper() {
        const xwiper = new XWiper("#imageContainer");
        xwiper.onSwipeLeft(() => app.drawNextImage());
        xwiper.onSwipeRight(() => app.drawPrevImage());
    }
    _setEventHandlers() {
        document.addEventListener("keydown", (event) => {
            switch (event.code) {
              case "KeyR":
                this.drawRandomImage();
                break;
              case "ArrowLeft":
                this.drawPrevImage();
                break;
              case "ArrowRight":
                thsi.drawNextImage();
                break;
              default:
                break;
            }
          });    
    }
    getGalleries() {
      return this.api.getGalleries().then((data) => {
        this.data.galleries = data;
        return data;
      });
    }
    getImages() {
      const settings = this.data.settings;
  
      return this.api
        .getImages(settings.selected_gallery, settings.show_mode)
        .then((data) => {
          if (data.length  == 0) {
            return Promise.reject(new Error("selected gallery did't return any image"))
          } 
          for (let i = 0; i < length; i++) {
            data[0].mod_date = new Date(data[0].mod_date);
          }
          data.sort((a, b) => {
            return invertComparsion(compareValues(a.mod_date, b.mod_date));
          });
          this.data.images = data;
          this.data.currentImageIndex = -1;
          return data;
        })
        .catch((error) => this.imageDrawer.drawError(error));
    }
    getSettings() {
      return this.api.getSettings().then((data) => {
        console.log(data);
        this.data.settings = data;
        return data;
      });
    }
    saveSettings(settings) {
      return this.api
        .saveSettings(settings)
        .then((response) => {
          if (response.ok) {
            this.data.settings = settings;
            return this.getImages();
          }
        })
        .then(() => true);
    }
    async markImage() {
      const settings = this.data.settings;
      const currImage = this.data.currentImage;
  
      const img_info = await this.api.markImage(
        settings.selected_gallery,
        currImage.name
      );
  
      if (settings.show_mode == "unmarked") {
        this.deleteImageFromImages(currImage);
        this.drawRandomImage();
      } else {
        const images = this.data.images;
        const idx = images.indexOf(currImage);
        images[idx] = img_info;
        this.data.currentImage = img_info;
        this.redraw();
      }
    }
    deleteImageFromImages(image) {
      const images = this.data.images;
      const idx = images.indexOf(image);
      if (idx >= 0) {
        images.splice(idx, 1);
      }
    }
    deleteImage() {
      this.api
        .deleteImage(
          this.data.settings.selected_gallery,
          this.data.currentImage.name
        )
        .then((response) => {
          if (response.ok) {
            this.deleteImageFromImages(this.data.currentImage);
            // compensate index
            this.redraw();
          }
        });
    }
    getRandomImageIndex() {
      const images = this.data.images;
  
      return Math.floor(Math.random() * images.length);
    }
    drawRandomImage() {
      this.data.currentImageIndex = this.getRandomImageIndex();
  
      this.redraw();
    }
    drawPrevImage() {
      const idx = this.data.currentImageIndex;
  
      if (idx - 1 < 0) {
        return;
      }
      this.data.currentImageIndex--;
      this.redraw();
    }
    drawNextImage() {
      const idx = this.data.currentImageIndex;
  
      if (idx + 1 == this.data.images.length) {
        return;
      }
  
      this.data.currentImageIndex++;
      this.redraw();
    }
    redraw() {
      this.data.currentImage = this.data.images[this.data.currentImageIndex];
      // this.drawImage(this.data.currentImage);
      const imgInfo = {
        image: this.data.currentImage,
        index: this.data.currentImageIndex,
        count: this.data.images.length,
      };
  
      this.imageDrawer.drawImage(imgInfo);
    }
    start() {
      this.getSettings()
        .then((settings) => {
          if (settings.show_mode && settings.selected_gallery) {
            return this.getImages();
          } else {
            return Promise.reject(new Error("pick settings in sidenav"));
          }
        })
        .then((images) => this.drawNextImage())
        .catch((err) => this.imageDrawer.drawError(err.message));
    }
  };