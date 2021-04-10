import XWiper from "xwiper";
import api from "./api";
import Sidenav from "./components/sidenav.js";
import ImageDrawer from "./components/image-drawer.js";
import { ImageInfo, PickerSettings } from "./models";

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

    // special debug settings
    this.debug = {
      fakeDelete: true, // detect that image will delete only from data.images
    };

    this.data = {
      /** @type {string[]} */
      galleries: [],
      /** @type {PickerSettings} */
      settings: null,
      /** @type {ImageInfo[]} */
      images: [],
      currentImageIndex: -1,
    };

    this._setXWiper();
    this._setEventHandlers();
    this.start();
  }
  _setXWiper() {
    const xwiper = new XWiper("#imageContainer");
    xwiper.onSwipeLeft(() => this.drawNextImage());
    xwiper.onSwipeRight(() => this.drawPrevImage());
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
          this.drawNextImage();
          break;
        default:
          break;
      }
    });

    window.addEventListener("popstate", async (event) => {
      const state = event.state;
      this.popAppStateFromHistory(state);

      console.log("popped state is ", state);
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
        if (data.length == 0) {
          return Promise.reject(
            new Error("selected gallery did't return any image")
          );
        }
        // for (let i = 0; i < length; i++) {
        //   data[0].mod_date = new Date(data[0].mod_date);
        // }
        data.sort((a, b) => {
          return invertComparsion(compareValues(a.mod_date, b.mod_date));
        });
        this.data.images = data;
        this.data.currentImageIndex = -1; // reset index
        return data;
      });
    //.catch((error) => this.imageDrawer.drawError(error));
  }
  async getImagesAndDraw() {
    await this.getImages();
    this.drawNextImage();
  }
  /** fetch settings from api */
  async fetchSettings() {
    const data = await this.api.getSettings();
    this.settings = data;
    return data;
  }
  get settings() {
    return this.data.settings;
  }
  set settings(value) {
    this.data.settings = value;
  }
  loadSettings() {
    if (history.state) {
      return Promise.resolve(this._loadSettingsFromHistoryState(history.state));
    } else {
      return this.fetchSettings();
    }
  }
  _loadSettingsFromHistoryState(state) {
    return state.settings;
  }
  /**
   * save settings via api
   * @param {PickerSettings} settings
   */
  async saveSettings(settings) {
    if(settings.isEqual(this.settings)) {
      return true;
    }

    const response = await this.api.saveSettings(settings);
    
    if (response.ok) {
        this.settings = settings;
        await this.getImagesAndDraw();
    }
  
    return true;
  }
  settingsChanged(newSettings) {
    const newSelGallery = newSettings.selected_gallery;
    const newShowMode = newSettings.show_mode;

    if (!newSettings) {
      return false;
    }

    if (!this.settings && newSettings) {
      return true;
    }

    if (
      this.settings.selected_gallery != newSelGallery ||
      this.settings.show_mode != newShowMode
    ) {
      return true;
    }

    return false;
  }
  /**
   * Добавляет в стейт признак, что там теперь невалидные
   * данные, ктороые нужно заменить текущими, а не создавать новый стейт
   */
  markHistoryStateInvalid() {
    if (history.state) {
      let currState = history.state;
      currState.invalid = true;
      history.replaceState(currState, "");
    }
  }
  get isHistoryStateInvalid() {
    return history.state && history.state.invalid;
  }
  appStateChanged() {
    if (!history.state) {
      return false;
    }

    return (
      !this.settings.isEqual(history.state.settings) ||
      history.state.currentImageUrl != this.getCurrentImage().url
    );
  }
  pushAppStateToHistory(replace = false) {
    // формируем объект
    const appState = {
      settings: this.settings,
      currentImageUrl: this.getCurrentImage().url,
    };

    // Если нету стейта, то скорее всего это первая закгзка приложения
    // и нам нужно будет заменить пустой текущим, чтобы работала история
    if (!history.state) {
      console.log("push initial state ", appState);
      history.replaceState(appState, "");
      // если наш стейт помечен невалидным, то тоже заменим его
    } else if (this.isHistoryStateInvalid) {
      console.log("replace invalid state ", appState);
      history.replaceState(appState, "");
    } else if (replace) {
      console.log("replace state");
      history.replaceState(appState, "");
    } else if (!this.appStateChanged()) {
      console.log("state doesn't change");
    } else {
      console.log("push new state ", appState);
      history.pushState(appState, "");
    }
  }
  // TODO Need validation
  async popAppStateFromHistory(state) {
    // если никакого стейта нет
    if (!state) {
      return;
    }

    // если настройки поменялись, заново загрузим картинки
    if (!this.settings || !this.settings.isEqual(state.settings)) {
      this.settings = new PickerSettings(state.settings);
      await this.getImages();
    }
    // проверим что сохраненный url есть в этих картинках
    const foundImg = this.data.images.find((elem, idx) => {
      if (elem.url == state.currentImageUrl) {
        this.data.currentImageIndex = idx;
        return true;
      }
    });
    if (!foundImg) {
      this.markHistoryStateInvalid();
      this.data.currentImageIndex = -1;
      this.drawNextImage();
    }

    this.redraw();
  }
  // TODO !!! CHECK HERE
  async markImage() {
    const currImage = this.getCurrentImage();

    const img_info = await this.api.markImage(
      this.settings.selected_gallery,
      currImage.name
    );

    if (this.settings.show_mode == "unmarked") {
      this.deleteImageFromImages(currImage);
      this.drawRandomImage();
    } else {
      const images = this.data.images;
      const idx = images.indexOf(currImage);
      images[idx] = img_info;
      this.pushAppStateToHistory(true);
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
  _fakeDelete() {
    const currentImage = this.getCurrentImage();
    this.deleteImageFromImages(currentImage);
    
    this.markHistoryStateInvalid();
    this.drawNextImage();
  }
  async deleteImage() {
    if (this.debug.fakeDelete) {
      this._fakeDelete();

      return;
    }

    const currentImage = this.getCurrentImage();
    const response = await this.api
      .deleteImage(this.settings.selected_gallery, currentImage.name)
    
        if (response.ok) {
          this.deleteImageFromImages(currentImage);
          // compensate index
          this.markHistoryStateInvalid();
          this.drawNextImage();
        }
  }
  /** возвращает изображение по текущему индексу */
  getCurrentImage() {
    const idx = this.data.currentImageIndex;

    // correct if needed
    if (idx < 0) {
      this.data.currentImageIndex = 0; // set to first
    } else if (idx >= this.data.images.length) {
      this.data.currentImageIndex = this.data.images.length - 1;
    }

    return this.data.images[this.data.currentImageIndex];
  }
  getRandomImageIndex() {
    const images = this.data.images;

    return Math.floor(Math.random() * images.length);
  }
  drawRandomImage() {
    this.data.currentImageIndex = this.getRandomImageIndex();

    this.pushAppStateToHistory();

    this.redraw();
  }
  drawPrevImage() {
    const idx = this.data.currentImageIndex;

    if (idx - 1 < 0) {
      return;
    }
    this.data.currentImageIndex--;
    this.pushAppStateToHistory();
    this.redraw();
  }
  drawNextImage() {
    const idx = this.data.currentImageIndex;

    if (idx + 1 == this.data.images.length) {
      return;
    }

    this.data.currentImageIndex++;
    this.pushAppStateToHistory();
    this.redraw();
  }
  /**
   * ВЫполняет отрисовку изображения по тек индексу
   */
  redraw() {
    const currentImage = this.getCurrentImage();

    this.imageDrawer.drawImage({
      image: currentImage,
      index: this.data.currentImageIndex,
      count: this.data.images.length,
    });
  }
  detectDebugSettings() {
    const locURrl = new URL(window.location);

    if (locURrl.searchParams.has("fakedel")) {
      this.debug.fakeDelete = true;
      console.warn("!fake delete on!");
    } else {
      this.debug.fakeDelete = false;
    }
  }
  async start() {
    //this.detectDebugSettings();
    if(history.state) {
      await this.popAppStateFromHistory(history.state);
      return
    }

    const settings = await this.fetchSettings();
    if (!this.settings.selected_gallery) {
      this.imageDrawer.drawError("Pick gallery in sidenav");
      return;
    }

    await this.getImagesAndDraw();
  }
}
