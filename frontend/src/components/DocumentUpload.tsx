import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, FileText, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";

interface DocumentUploadProps {
  onDocumentUploaded: () => void;
}

export const DocumentUpload = ({ onDocumentUploaded }: DocumentUploadProps) => {
  const [files, setFiles] = useState<File[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("general");
  const [tags, setTags] = useState("");
  const [uploading, setUploading] = useState(false);
  const { toast } = useToast();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const uploadDocument = async () => {
    if (!files.length || !title.trim()) {
      toast({
        title: "Lỗi",
        description: "Vui lòng chọn file và nhập tiêu đề",
        variant: "destructive"
      });
      return;
    }

    setUploading(true);
    
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        toast({
          title: "Lỗi",
          description: "Vui lòng đăng nhập để tải lên tài liệu",
          variant: "destructive"
        });
        return;
      }

      for (const file of files) {
        const fileExt = file.name.split('.').pop();
        const fileName = `${Date.now()}-${Math.random().toString(36).substring(2)}.${fileExt}`;
        const filePath = `${user.id}/${fileName}`;

        // Upload file to storage
        const { error: uploadError } = await supabase.storage
          .from('documents')
          .upload(filePath, file);

        if (uploadError) {
          throw uploadError;
        }

        // Save metadata to database
        const { error: dbError } = await supabase
          .from('documents')
          .insert({
            user_id: user.id,
            title: files.length > 1 ? `${title} - ${file.name}` : title,
            description,
            file_name: file.name,
            file_path: filePath,
            file_size: file.size,
            file_type: file.type,
            category,
            tags: tags ? tags.split(',').map(tag => tag.trim()) : []
          });

        if (dbError) {
          throw dbError;
        }
      }

      toast({
        title: "Thành công",
        description: `Đã tải lên ${files.length} tài liệu thành công`
      });

      // Reset form
      setFiles([]);
      setTitle("");
      setDescription("");
      setCategory("general");
      setTags("");
      onDocumentUploaded();

    } catch (error: any) {
      console.error('Upload error:', error);
      toast({
        title: "Lỗi",
        description: error.message || "Có lỗi xảy ra khi tải lên tài liệu",
        variant: "destructive"
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="title">Tiêu đề *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Nhập tiêu đề tài liệu"
            />
          </div>

          <div>
            <Label htmlFor="description">Mô tả</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả ngắn về tài liệu"
              rows={3}
            />
          </div>

          <div>
            <Label htmlFor="category">Danh mục</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="general">Chung</SelectItem>
                <SelectItem value="technical">Kỹ thuật</SelectItem>
                <SelectItem value="user-manual">Hướng dẫn sử dụng</SelectItem>
                <SelectItem value="datasheet">Datasheet</SelectItem>
                <SelectItem value="report">Báo cáo</SelectItem>
                <SelectItem value="procedure">Quy trình</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="tags">Tags (cách nhau bằng dấu phẩy)</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="ví dụ: UPS, kỹ thuật, hướng dẫn"
            />
          </div>
        </div>

        <div>
          <Label htmlFor="files">Chọn file *</Label>
          <div className="mt-2">
            <Input
              id="files"
              type="file"
              multiple
              onChange={handleFileSelect}
              accept=".pdf,.doc,.docx,.txt,.md"
              className="mb-4"
            />
            
            {files.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">File đã chọn:</h4>
                {files.map((file, index) => (
                  <Card key={index}>
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-primary" />
                          <div>
                            <p className="text-sm font-medium">{file.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <Button 
        onClick={uploadDocument} 
        disabled={uploading || !files.length || !title.trim()}
        className="w-full"
      >
        <Upload className="h-4 w-4 mr-2" />
        {uploading ? "Đang tải lên..." : `Tải lên ${files.length} tài liệu`}
      </Button>
    </div>
  );
};