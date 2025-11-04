import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Sparkles, Wand2, Image, Download, Star, History, Copy, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [activeTab, setActiveTab] = useState("form");
  const [formData, setFormData] = useState({
    subject: "",
    setting: "",
    lighting: "",
    camera_angle: "",
    style: "",
    mood: "",
    additional_details: ""
  });
  const [aiPrompt, setAiPrompt] = useState("");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [history, setHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    fetchHistory();
    fetchFavorites();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/prompts/history`);
      setHistory(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/prompts/favorites`);
      setFavorites(response.data);
    } catch (error) {
      console.error("Error fetching favorites:", error);
    }
  };

  const handleFormChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const generatePromptFromForm = async () => {
    if (!formData.subject.trim()) {
      toast.error("Please enter a subject for your image");
      return;
    }

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/prompts/generate-form`, formData);
      setGeneratedPrompt(response.data.prompt);
      toast.success("Prompt generated successfully!");
    } catch (error) {
      toast.error("Failed to generate prompt: " + (error.response?.data?.detail || error.message));
    } finally {
      setIsGenerating(false);
    }
  };

  const enhancePromptWithAI = async () => {
    if (!aiPrompt.trim()) {
      toast.error("Please enter a basic prompt to enhance");
      return;
    }

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/prompts/enhance`, { basic_prompt: aiPrompt });
      setGeneratedPrompt(response.data.prompt);
      toast.success("Prompt enhanced with AI!");
    } catch (error) {
      toast.error("Failed to enhance prompt: " + (error.response?.data?.detail || error.message));
    } finally {
      setIsGenerating(false);
    }
  };

  const generateImage = async () => {
    if (!generatedPrompt.trim()) {
      toast.error("Please generate a prompt first");
      return;
    }

    setIsGeneratingImage(true);
    try {
      const response = await axios.post(`${API}/prompts/generate-image`, { prompt: generatedPrompt });
      setGeneratedImage(response.data);
      
      // Save to history
      await axios.post(`${API}/prompts/save`, {
        prompt_text: generatedPrompt,
        prompt_type: activeTab,
        parameters: activeTab === "form" ? formData : { basic_prompt: aiPrompt },
        image_data: response.data.image_data
      });
      
      fetchHistory();
      toast.success("Image generated successfully!");
    } catch (error) {
      toast.error("Failed to generate image: " + (error.response?.data?.detail || error.message));
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const copyPrompt = () => {
    navigator.clipboard.writeText(generatedPrompt);
    toast.success("Prompt copied to clipboard!");
  };

  const downloadImage = () => {
    if (!generatedImage) return;
    
    const link = document.createElement('a');
    link.href = `data:${generatedImage.mime_type};base64,${generatedImage.image_data}`;
    link.download = `ad-image-${Date.now()}.png`;
    link.click();
    toast.success("Image downloaded!");
  };

  const toggleFavorite = async (promptId) => {
    try {
      await axios.post(`${API}/prompts/${promptId}/favorite`);
      fetchHistory();
      fetchFavorites();
      toast.success("Favorite updated!");
    } catch (error) {
      toast.error("Failed to update favorite");
    }
  };

  const loadHistoryItem = (item) => {
    setGeneratedPrompt(item.prompt_text);
    if (item.image_data) {
      setGeneratedImage({ image_data: item.image_data, mime_type: "image/png" });
    }
    if (item.prompt_type === "form" && item.parameters) {
      setFormData(item.parameters);
      setActiveTab("form");
    } else if (item.prompt_type === "ai" && item.parameters?.basic_prompt) {
      setAiPrompt(item.parameters.basic_prompt);
      setActiveTab("ai");
    }
    setShowHistory(false);
    toast.success("Loaded from history");
  };

  return (
    <div className="app-container" style={{ maxWidth: "1600px", margin: "0 auto" }}>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="heading-font text-5xl lg:text-6xl font-bold mb-4 gradient-text" data-testid="page-title">
          Master Prompt Generator
        </h1>
        <p className="text-lg text-gray-600" data-testid="page-subtitle">
          Create photorealistic ad images with AI-powered prompts
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Prompt Generation */}
          <Card className="card-glass" data-testid="prompt-generator-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-2xl heading-font">
                <Sparkles className="w-6 h-6 text-purple-600" />
                Generate Your Prompt
              </CardTitle>
              <CardDescription>Choose your method to create photorealistic prompts</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab} data-testid="prompt-tabs">
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="form" data-testid="form-tab">Form Builder</TabsTrigger>
                  <TabsTrigger value="ai" data-testid="ai-tab">AI Enhancer</TabsTrigger>
                </TabsList>

                <TabsContent value="form" className="space-y-4" data-testid="form-content">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="subject">Subject *</Label>
                      <Input
                        id="subject"
                        data-testid="subject-input"
                        placeholder="e.g., luxury watch, coffee cup, smartphone"
                        value={formData.subject}
                        onChange={(e) => handleFormChange("subject", e.target.value)}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="setting">Setting</Label>
                      <Input
                        id="setting"
                        data-testid="setting-input"
                        placeholder="e.g., marble table, modern office"
                        value={formData.setting}
                        onChange={(e) => handleFormChange("setting", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lighting">Lighting</Label>
                      <Select value={formData.lighting} onValueChange={(value) => handleFormChange("lighting", value)}>
                        <SelectTrigger id="lighting" data-testid="lighting-select">
                          <SelectValue placeholder="Select lighting" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="natural">Natural</SelectItem>
                          <SelectItem value="studio">Studio</SelectItem>
                          <SelectItem value="golden_hour">Golden Hour</SelectItem>
                          <SelectItem value="dramatic">Dramatic</SelectItem>
                          <SelectItem value="soft">Soft</SelectItem>
                          <SelectItem value="backlit">Backlit</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="camera">Camera Angle</Label>
                      <Select value={formData.camera_angle} onValueChange={(value) => handleFormChange("camera_angle", value)}>
                        <SelectTrigger id="camera" data-testid="camera-select">
                          <SelectValue placeholder="Select angle" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="eye_level">Eye Level</SelectItem>
                          <SelectItem value="top_down">Top Down</SelectItem>
                          <SelectItem value="close_up">Close Up</SelectItem>
                          <SelectItem value="wide">Wide</SelectItem>
                          <SelectItem value="45_degree">45 Degree</SelectItem>
                          <SelectItem value="low_angle">Low Angle</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="style">Style</Label>
                      <Select value={formData.style} onValueChange={(value) => handleFormChange("style", value)}>
                        <SelectTrigger id="style" data-testid="style-select">
                          <SelectValue placeholder="Select style" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="minimalist">Minimalist</SelectItem>
                          <SelectItem value="luxury">Luxury</SelectItem>
                          <SelectItem value="vibrant">Vibrant</SelectItem>
                          <SelectItem value="muted">Muted</SelectItem>
                          <SelectItem value="modern">Modern</SelectItem>
                          <SelectItem value="rustic">Rustic</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="mood">Mood</Label>
                      <Input
                        id="mood"
                        data-testid="mood-input"
                        placeholder="e.g., energetic, calm, sophisticated"
                        value={formData.mood}
                        onChange={(e) => handleFormChange("mood", e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="details">Additional Details</Label>
                    <Textarea
                      id="details"
                      data-testid="details-textarea"
                      placeholder="Any specific details like colors, textures, background elements..."
                      value={formData.additional_details}
                      onChange={(e) => handleFormChange("additional_details", e.target.value)}
                      rows={3}
                    />
                  </div>

                  <Button 
                    className="w-full btn-generate" 
                    onClick={generatePromptFromForm}
                    disabled={isGenerating}
                    data-testid="generate-form-button"
                  >
                    {isGenerating ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
                    ) : (
                      <><Wand2 className="w-4 h-4 mr-2" /> Generate Prompt</>
                    )}
                  </Button>
                </TabsContent>

                <TabsContent value="ai" className="space-y-4" data-testid="ai-content">
                  <div className="space-y-2">
                    <Label htmlFor="ai-prompt">Basic Prompt</Label>
                    <Textarea
                      id="ai-prompt"
                      data-testid="ai-prompt-textarea"
                      placeholder="Describe your ad image idea... e.g., 'a coffee cup on a cozy morning table'"
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      rows={6}
                    />
                  </div>
                  <p className="text-sm text-gray-500">
                    Our AI will transform your basic idea into a detailed, photorealistic prompt optimized for generating stunning ad images.
                  </p>
                  <Button 
                    className="w-full btn-generate" 
                    onClick={enhancePromptWithAI}
                    disabled={isGenerating}
                    data-testid="enhance-ai-button"
                  >
                    {isGenerating ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Enhancing...</>
                    ) : (
                      <><Sparkles className="w-4 h-4 mr-2" /> Enhance with AI</>
                    )}
                  </Button>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Generated Prompt */}
          {generatedPrompt && (
            <Card className="card-glass" data-testid="generated-prompt-card">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2 heading-font">
                    <Sparkles className="w-5 h-5 text-purple-600" />
                    Generated Prompt
                  </span>
                  <Button variant="outline" size="sm" onClick={copyPrompt} data-testid="copy-prompt-button">
                    <Copy className="w-4 h-4 mr-1" /> Copy
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 p-4 rounded-lg mb-4" data-testid="generated-prompt-text">
                  <p className="text-sm leading-relaxed text-gray-700">{generatedPrompt}</p>
                </div>
                <Button 
                  className="w-full btn-generate" 
                  onClick={generateImage}
                  disabled={isGeneratingImage}
                  data-testid="generate-image-button"
                >
                  {isGeneratingImage ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating Image...</>
                  ) : (
                    <><Image className="w-4 h-4 mr-2" /> Generate Image</>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Generated Image */}
          {generatedImage && (
            <Card className="card-glass" data-testid="generated-image-card">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2 heading-font">
                    <Image className="w-5 h-5 text-purple-600" />
                    Generated Image
                  </span>
                  <Button variant="outline" size="sm" onClick={downloadImage} data-testid="download-image-button">
                    <Download className="w-4 h-4 mr-1" /> Download
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="image-preview">
                  <img 
                    src={`data:${generatedImage.mime_type};base64,${generatedImage.image_data}`}
                    alt="Generated ad image"
                    className="w-full h-auto"
                    data-testid="generated-image"
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* History/Favorites Toggle */}
          <Card className="card-glass" data-testid="history-card">
            <CardHeader>
              <div className="flex gap-2">
                <Button
                  variant={showHistory ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowHistory(true)}
                  className="flex-1"
                  data-testid="history-tab-button"
                >
                  <History className="w-4 h-4 mr-1" /> History
                </Button>
                <Button
                  variant={!showHistory ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowHistory(false)}
                  className="flex-1"
                  data-testid="favorites-tab-button"
                >
                  <Star className="w-4 h-4 mr-1" /> Favorites
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-3">
                  {(showHistory ? history : favorites).length === 0 ? (
                    <p className="text-center text-gray-400 py-8" data-testid="empty-message">
                      {showHistory ? "No history yet" : "No favorites yet"}
                    </p>
                  ) : (
                    (showHistory ? history : favorites).map((item) => (
                      <div 
                        key={item.id} 
                        className="history-item group relative"
                        onClick={() => loadHistoryItem(item)}
                        data-testid={`history-item-${item.id}`}
                      >
                        {item.image_data && (
                          <img 
                            src={`data:image/png;base64,${item.image_data}`}
                            alt="Preview"
                            className="w-full h-32 object-cover rounded-lg mb-2"
                          />
                        )}
                        <p className="text-sm text-gray-600 line-clamp-2 mb-2">{item.prompt_text}</p>
                        <div className="flex items-center justify-between">
                          <span className="badge">{item.prompt_type}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleFavorite(item.id);
                            }}
                            data-testid={`favorite-button-${item.id}`}
                          >
                            <Star className={`w-4 h-4 ${item.is_favorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Home;