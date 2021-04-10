import "./styles/main.css";
import App from './app.js';

const app = new App()

// TODO написать одно событие с делегированием на контейнер
function ImageButtons(app) {
  this.app = app;
  this.buttonsPanel = document.querySelector(".buttons-panel");
  
  this.randomButton = document.getElementById("random");
  this.randomButton.addEventListener("click", (e) => {
    e.preventDefault();
    this.app.drawRandomImage();
  });

  this.nextButton = document.getElementById("next");
  this.nextButton.addEventListener("click", (e) => {
    e.preventDefault();
    this.app.drawNextImage();
  });

  this.prevButton = document.getElementById("prev");
  this.prevButton.addEventListener("click", (e) => {
    e.preventDefault();
    this.app.drawPrevImage();
  });

  // FIXME temporary switch to usual confirm
  /*this.deleteButton = document.getElementById("confirmDelete");
  this.deleteButton.addEventListener("click", () => {
      console.log("del");
      $("#deleteModal").modal("hide");
      this.app.deleteImage();
    
  }); */
  this.deleteButton = document.getElementById("delete");
  this.deleteButton.addEventListener("click", (e) => {
    e.preventDefault();
    if (confirm("Are you sure to delete?")) {
      this.app.deleteImage();
    }
  });

  this.markButton = document.getElementById("mark");
  this.markButton.addEventListener("click", (e) => {
    e.preventDefault();
    if (!this.app.getCurrentImage().marked) {
      this.app.markImage();
    }
  });
}

const panel = new ImageButtons(app);

