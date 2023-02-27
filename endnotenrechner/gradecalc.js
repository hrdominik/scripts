const defaultWinfoModules = [
    { name: "Programmierung", semester: 1, ects: 8 },
    { name: "Programmiersprachen", semester: 1, ects: 4 },
    { name: "Modellierung", semester: 1, ects: 8 },
    { name: "Grundlagen betrieblicher Informationssysteme", semester: 1, ects: 5 },
    { name: "Grundlagen des Informationsmanagements", semester: 1, ects: 5 },
    { name: "Software Engineering", semester: 2, ects: 5 },
    { name: "Grundlagen von Dispositions und Entscheidungsunterstützungssystemen", semester: 2, ects: 5 },
    { name: "Grundlagen von Managementinformationssystemen", semester: 2, ects: 5 },
    { name: "Grundlagen der VWL", semester: 2, ects: 10 },
    { name: "Statistik für Winfos", semester: 2, ects: 5 },
    { name: "Analysis für Informatiker", semester: 3, ects: 8 },
    { name: "Softwaretechnikpraktikum", semester: 3, ects: 8 },
    { name: "Grundlagen von Social Media und Kooperativen Technologien", semester: 3, ects: 5 },
    { name: "Management", semester: 3, ects: 5 },
    { name: "Einführung in die Wirtschaftswissenschaften", semester: 3, ects: 5 },
    { name: "Datenstrukturen und Algorithmen", semester: 4, ects: 9 },
    { name: "Datenbanksysteme", semester: 4, ects: 5 },
    { name: "Winfo oder WiWi Wahlmodul", semester: 4, ects: 5 },
    { name: "Taxation, Accounting and Finance", semester: 4, ects: 10 },
    { name: "Info Wahlmodul", semester: 5, ects: 6 },
    { name: "Winfo Wahlmodul", semester: 5, ects: 5 },
    { name: "Methodenmodul Winfo", semester: 5, ects: 5 },
    { name: "Methodenmodul Winfo", semester: 5, ects: 5 },
    { name: "Methodenmodul Winfo", semester: 5, ects: 5 },
    { name: "Studienarbeit", semester: 5, ects: 5 },
    { name: "Winfo Wahlmodul", semester: 6, ects: 10 },
    { name: "Bachelorarbeit inkl. Kolloquium", semester: 6, ects: 14 },
    { name: "WiWi Wahlmodul", semester: 6, ects: 5 }
  ];
  let modules = [];
  function isProfPhase(module) {
    return module.semester > 2;
  }
  function calcWeight(module) {
    if (!document.getElementById("graduationSwitch").checked) {
      if (module.semester == 6 && module.ects == 14) {
        // is Abschlussarbeit
        return module.ects * 4;
      } else {
        if (isProfPhase(module)) {
          return module.ects * 2;
        } else {
          return module.ects * 1;
        }
      }
    } else {
      if (module.semester == 4 && (module.ects == 29 || module.ects == 30)) {
        // is Abschlussarbeit
        return module.ects * 2;
      } else {
        return module.ects * 1;
      }
    }
  }
  
  function calcFinalGrade() {
    let sum = 0;
    let weight = 0;
    for (let m of modules) {
      sum += m.grade * calcWeight(m);
      weight += calcWeight(m);
    }
    return sum / weight;
  }
  
  function validateModule(module, endnoteModule) {
    if (module.name == "") {
      endnoteModule.classList.add("is-invalid");
      return false;
    }
    if (module.semester == 0 || module.semester > 6) {
      endnoteModule.classList.add("is-invalid");
      return false;
    }
    if ((module.ects < 4 || module.ects > 10) && module.ects != 14) {
      endnoteModule.classList.add("is-invalid");
      return false;
    }
    if (!module.grade || module.grade < 1 || module.grade > 4) {
      endnoteModule.classList.add("is-invalid");
      return false;
    }
    return true;
  }
  
  function calcGrade() {
    if (modules.length < 2) {
      const error = document.getElementById("error");
      error.innerText = "Füge zunächst mindestens zwei Module hinzu!";
      return;
    }
    let sumECTS = 0;
    for (let m in modules) {
      let mElem = document.getElementById("module-table-inner").children[m];
      mElem.className = "module row";
      modules[m].name = mElem.querySelector("input[name='moduleName']").value;
      modules[m].semester = parseInt(mElem.querySelector("[name='semester']").value);
      modules[m].ects = parseInt(mElem.querySelector("[name='ects']").value);
      modules[m].grade = parseFloat(mElem.querySelector("input[name='grade']").value);
      if (!validateModule(modules[m], mElem)) {
        const error = document.getElementById("error");
        error.innerText = "Überprüfe deine Eingabe";
        return;
      }
      const error = document.getElementById("error");
      error.innerText = "";
      sumECTS += modules[m].ects;
    }
    const resultGrade = calcFinalGrade(modules);
    const endnoteResult = document.getElementById("result");
    endnoteResult.innerText = resultGrade;
    const endnoteResultECTS = document.getElementById("result-ects");
    endnoteResultECTS.innerText = sumECTS;
  
    const endnoteResultContainer = document.getElementById("result-container-wrapper");
    endnoteResultContainer.style = "display: block;";
  }
  
  function getNewModuleElem(values) {
    const endnoteModule = document.createElement("div");
    endnoteModule.className = "module row";
    endnoteModule.id = "module-" + (modules.length - 1); // deprecated
  
    const endnoteModule_name = document.createElement("input");
    endnoteModule_name.type = "text";
    endnoteModule_name.className = "module-item module-item-name col";
    endnoteModule_name.name = "moduleName";
    endnoteModule_name.placeholder = "Modulname";
    if (values) [(endnoteModule_name.value = values.name)];
    const endnoteModule_semester = document.createElement("select");
    // endnoteModule_semester.type = "number";
    endnoteModule_semester.className = "module-item col";
    endnoteModule_semester.name = "semester";
    // endnoteModule_semester.placeholder = "Semester";
    const semesterOpt = [
      { value: 1, label: "1. Semester" },
      { value: 2, label: "2. Semester" },
      { value: 3, label: "3. Semester" },
      { value: 4, label: "4. Semester" },
      { value: 5, label: "5. Semester" },
      { value: 6, label: "6. Semester" }
    ];
    for (let opt of semesterOpt) {
      let option = document.createElement("option");
      option.value = opt.value;
      option.text = opt.label;
      if (
        (opt.value == 5 && document.getElementById("graduationSwitch").checked) ||
        (opt.value == 6 && document.getElementById("graduationSwitch").checked)
      ) {
        // do nothing
      } else {
        endnoteModule_semester.appendChild(option);
      }
    }
    if (values) [(endnoteModule_semester.value = values.semester)];
    const endnoteModule_ects = document.createElement("select");
    // endnoteModule_ects.type = "number";
    endnoteModule_ects.className = "module-item col";
    endnoteModule_ects.name = "ects";
    // endnoteModule_ects.placeholder = "ECTS";
    const ectsOpt = [
      { value: 4, label: "4" },
      { value: 5, label: "5" },
      { value: 6, label: "6" },
      { value: 8, label: "8" },
      { value: 9, label: "9" },
      { value: 10, label: "10" },
      { value: 14, label: "14" },
      { value: 29, label: "29" },
      { value: 30, label: "30" }
    ];
    for (let opt of ectsOpt) {
      let option = document.createElement("option");
      option.value = opt.value;
      option.text = opt.label;
      if (
        (opt.value == 14 && document.getElementById("graduationSwitch").checked) ||
        (opt.value == 29 && !document.getElementById("graduationSwitch").checked) ||
        (opt.value == 30 && !document.getElementById("graduationSwitch").checked)
      ) {
        // do nothing
      } else {
        endnoteModule_ects.appendChild(option);
      }
    }
    if (values) [(endnoteModule_ects.value = values.ects)];
    const endnoteModule_grade = document.createElement("input");
    endnoteModule_grade.type = "number";
    endnoteModule_grade.className = "module-item col";
    endnoteModule_grade.name = "grade";
    endnoteModule_grade.placeholder = "Note";
    endnoteModule_grade.min = 1.0;
    endnoteModule_grade.max = 5.0;
    endnoteModule_grade.step = 0.1;
    if (values) [(endnoteModule_grade.value = values.grade)];
  
    const endnoteModule_remove = document.createElement("button");
    endnoteModule_remove.innerHTML = "Entfernen";
    endnoteModule_remove.className = "module-item module-item-del btn btn-primary col";
    endnoteModule_remove.onclick = function () {
      modules.splice(modules.indexOf(values), 1);
      endnoteModule.remove();
    };
  
    endnoteModule.appendChild(endnoteModule_name);
    endnoteModule.appendChild(endnoteModule_semester);
    endnoteModule.appendChild(endnoteModule_ects);
    endnoteModule.appendChild(endnoteModule_grade);
    endnoteModule.appendChild(endnoteModule_remove);
  
    return endnoteModule;
  }
  
  function addModule() {
    let module = {
      name: "",
      semester: 1,
      ects: 5
    };
    modules.push(module);
  
    const endnoteTable = document.getElementById("module-table-inner");
    endnoteTable.appendChild(getNewModuleElem(module));
  }
  
  function clearModules() {
    const endnoteTable = document.getElementById("module-table-inner");
    endnoteTable.innerHTML = "";
    const error = document.getElementById("error");
    error.innerText = "";
    const endnoteResult = document.getElementById("result");
    endnoteResult.innerText = "";
    const endnoteResultECTS = document.getElementById("result-ects");
    endnoteResultECTS.innerText = "";
  
    const endnoteResultContainer = document.getElementById("result-container-wrapper");
    endnoteResultContainer.style = "display: none;";
  }
  
  function initWithValues(values) {
    modules = values;
    clearModules();
    const endnoteTable = document.getElementById("module-table-inner");
    for (let m of modules) {
      const endnoteModule = getNewModuleElem(m);
      endnoteTable.appendChild(endnoteModule);
    }
  }
  
  function useWinfo() {
    initWithValues(defaultWinfoModules);
  }
  
  function importPlan() {
    let input = document.createElement("input");
    input.type = "file";
    const endnoteImportInput = document.getElementById("import-input");
    endnoteImportInput.appendChild(input);
    input.click();
    input.onchange = function () {
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = function () {
        const data = JSON.parse(reader.result);
        initWithValues(data);
      };
      reader.readAsText(file);
    };
    calcGrade();
  }
  
  function exportPlan() {
    let a = document.createElement("a");
    let file = new Blob([JSON.stringify(modules)], { type: "text/plain" });
    a.href = URL.createObjectURL(file);
    a.download = "fsrWinfo-Endnotenrechner-export.json";
    a.click();
  }
  
  function save2LocalStorage() {
    localStorage.setItem("fsr-winfo-endmodulrechner-module", JSON.stringify(modules));
    alert("Daten wurden gespeichert.");
  }
  
  function getFromLocalStorage() {
    let temp = JSON.parse(localStorage.getItem("fsr-winfo-endmodulrechner-module"));
    if (!temp) {
      alert("Keine Daten gefunden!");
    }
    initWithValues(temp);
    calcGrade();
  }
  