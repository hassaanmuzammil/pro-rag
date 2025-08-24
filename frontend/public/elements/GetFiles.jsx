import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileText } from "lucide-react"

export default function GetFiles() {
  return (
    <Card className="w-full max-w-md">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg font-medium">Files</CardTitle>
          <Badge variant="outline">{props.files?.length || 0} files</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
            {props.files?.map((file, idx) => (
                <div key={idx} className="flex items-center gap-2">
                <FileText className="h-4 w-4 opacity-70" />
                <span className="text-sm">{file}</span>
                </div>
            )) || (
                <div className="flex items-center gap-2 text-gray-500">
                <FileText className="h-4 w-4 opacity-70" />
                <span className="text-sm">No files</span>
                </div>
            )}
            </div>
      </CardContent>
    </Card>
  )
}