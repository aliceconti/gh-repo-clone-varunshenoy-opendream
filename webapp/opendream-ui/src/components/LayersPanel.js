import { useEffect, useState } from "react";
import { PlusCircle, Image } from "lucide-react";
import { Dropdown, Space } from "antd";
import ViewWorkflowButton from "./ViewWorkflowButton";
import LayerItem from "./LayerItem";
import LayerFormModal from "./LayerFormModal";

export const LayersPanel = ({ setImage, currentState, setCurrentState }) => {
  const [items, setItems] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState("");
  const [fields, setFields] = useState([]);
  const [required, setRequired] = useState([]);
  const [loading, setLoading] = useState(false);

  const showModal = (method) => {
    // make query to schema here
    const fetchData = async (method) => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/schema/" + method + "/"
        );
        const responseData = await response.json();
        let checkRequired = [];
        const cleanedResponseData = responseData.params.map((param, index) => {
          if (param["default"] === null) {
            checkRequired.push(param["name"]);
          }
          return {
            // TODO: this should be set to "filepicker" server-side whenever something is a path
            type: param["type"] || "input",
            label: param["name"],
            placeholder: param["default"] == null ? "" : param["default"],
          };
        });

        setRequired(checkRequired);

        console.log(cleanedResponseData);

        setFields(cleanedResponseData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData(method).then(() => {
      setSelectedMethod(method);
      setIsModalOpen(true);
    });
  };
  const handleOk = () => {
    // make query to backend here using selectedMethod and fields
    // setIsModalOpen(false);
  };
  const handleCancel = () => {
    setIsModalOpen(false);
  };

  const onFinish = (values) => {
    setLoading(true);
    console.log("Success:", values);

    let query = { params: [], options: {} };

    // Initialize the form data with the default values.
    for (const value of fields) {
      if (!required.includes(value.label)) {
        query["options"][value.label] = value.placeholder;
      }
    }

    // Iterate over values to fill in params and override defaults.
    for (const [key, value] of Object.entries(values)) {
      // if key is in required, add to params
      if (required.includes(key)) {
        query["params"].push(value);
      } else if (value !== undefined && value !== "") {
        query["options"][key] = value;
      }
    }

    console.log(query);

    const runOperation = async (method) => {
      try {
        // POST request using fetch with async/await
        const response = await fetch(
          "http://127.0.0.1:8000/operation/" + method + "/",
          {
            method: "POST",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
            body: JSON.stringify(query),
          }
        );

        const responseData = await response.json();
        console.log(responseData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    const getLayerData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/state/");
        const responseData = await response.json();
        console.log(responseData);

        setCurrentState(responseData["layers"].reverse());

        setImage(responseData["layers"][0]["image"]);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    runOperation(selectedMethod).then(() => {
      getLayerData().then(() => {
        setLoading(false);
        setIsModalOpen(false);
      });
    });
  };

  const onFinishFailed = (errorInfo) => {
    console.log("Failed:", errorInfo);
  };

  const titleCapitalize = (str) => {
    return str
      .split("_") // Split the string at underscores
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()) // Capitalize the first character of each word and make the rest lowercase
      .join(" "); // Join the words back together with space
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/available_operations/"
        );
        const responseData = await response.json();
        const cleanedResponseData = responseData.operators.map(
          (method, index) => {
            return {
              key: index,
              label: (
                <a onClick={() => showModal(method)}>
                  {titleCapitalize(method)}
                </a>
              ),
            };
          }
        );

        console.log(cleanedResponseData);

        setItems(cleanedResponseData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    console.log("fetching data");

    fetchData();

    const getLayerData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/state/");
        const responseData = await response.json();
        console.log(responseData);

        setCurrentState(responseData["layers"].reverse());

        setImage(responseData["layers"][0]["image"]);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    getLayerData();
  }, []);

  const fetchOperations = async () => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/available_operations/"
        );
        const responseData = await response.json();
        const cleanedResponseData = responseData.operators.map(
          (method, index) => {
            return {
              key: index,
              label: (
                <a onClick={() => showModal(method)}>
                  {titleCapitalize(method)}
                </a>
              ),
            };
          }
        );

        console.log(cleanedResponseData);

        setItems(cleanedResponseData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    console.log("fetching data");

    fetchData();
  };

  return (
    <div className="grid grid-cols-1">
      <LayerFormModal
        title={titleCapitalize(selectedMethod)}
        open={isModalOpen}
        handleOk={handleOk}
        handleCancel={handleCancel}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        fields={fields}
        loading={loading}
        currentState={currentState}
      />
      <section aria-labelledby="section-2-title">
        <div className="overflow-hidden rounded-md border border-zinc-200 bg-white">
          <div>
            <div class="p-6 flex justify-between items-center pb-2 border-b border-zinc-20 mb-3">
              <span class="text-left font-bold text-lg">Layers</span>
              <span class="text-right">
                <Space direction="vertical">
                  <Space wrap>
                    <Dropdown
                      menu={{ items }}
                      placement="bottom"
                      trigger="click"
                    >
                      <a
                        class="text-zinc-500 hover:text-zinc-900 hover:cursor-pointer"
                        onClick={fetchOperations}
                      >
                        <PlusCircle size={20}></PlusCircle>
                      </a>
                    </Dropdown>
                  </Space>
                </Space>
              </span>
            </div>
            {currentState.length === 0 && (
              <div class="p-6 flex justify-between items-center py-4">
                Add a new layer to begin.
              </div>
            )}
            {
              // iterate over currentState
              currentState.map((layer, index) => (
                <LayerItem
                  imgSrc={layer["image"]}
                  title={layer["id"]}
                  isMask={
                    layer["metadata"]["op"] === "mask" ||
                    layer["metadata"]["op"] === "sam"
                      ? true
                      : false
                  }
                  setImage={setImage}
                  setCurrentState={setCurrentState}
                />
              ))
            }
          </div>
        </div>
      </section>
      <a
        onClick={() => {
          const postImage = async (image) => {
            try {
              // POST request using fetch with async/await
              const response = await fetch("http://127.0.0.1:8000/add_layer/", {
                method: "POST",
                headers: {
                  Accept: "application/json",
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ image: image }),
              });
              const responseData = await response.json();

              console.log(responseData);
              setCurrentState(responseData["layers"].reverse());
              setImage(responseData["layers"][0]["image"]);
            } catch (error) {
              console.error("Error fetching data:", error);
            }
          };

          const handleImageUpload = (event) => {
            const file = event.target.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onloadend = () => {
              postImage(reader.result);
            };
          };

          const input = document.createElement("input");
          input.type = "file";
          input.accept = ".png, .jpg, .jpeg";
          input.onchange = handleImageUpload;
          input.click();
        }}
        className="flex cursor-pointer hover:bg-cyan-800 items-center justify-center rounded-md bg-cyan-700 w-full px-3.5 py-2.5 mt-4 text-sm font-semibold text-white shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-600"
      >
        Upload Image
        <Image size={18} class="ml-2"></Image>
      </a>
      {currentState.length > 0 && (
        <ViewWorkflowButton currentState={currentState} />
      )}
    </div>
  );
};
