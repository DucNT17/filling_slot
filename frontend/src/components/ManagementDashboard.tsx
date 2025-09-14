import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Folder, FolderOpen, Package, Settings } from "lucide-react";
import { CategoryManagement } from "./CategoryManagement";
import { ProductLineManagement } from "./ProductLineManagement";
import { ProductManagement } from "./ProductManagement";
import axios from "axios";

const API_BASE_URL = "http://52.64.205.176:8080/";

export const ManagementDashboard = () => {
    const [stats, setStats] = useState({
        categories: 0,
        productLines: 0,
        products: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const [categoriesRes, productLinesRes, productsRes] = await Promise.all([
                axios.get(`${API_BASE_URL}categories`),
                axios.get(`${API_BASE_URL}product-lines`),
                axios.get(`${API_BASE_URL}products`)
            ]);

            setStats({
                categories: categoriesRes.data.length,
                productLines: productLinesRes.data.length,
                products: productsRes.data.length
            });
        } catch (error) {
            console.error('Error fetching stats:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Quản lý Hệ thống</h1>
                    <p className="text-muted-foreground">
                        Quản lý danh mục, dòng sản phẩm và sản phẩm
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Settings className="h-5 w-5 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Cấu hình hệ thống</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Danh mục</CardTitle>
                        <Folder className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{loading ? "-" : stats.categories}</div>
                        <p className="text-xs text-muted-foreground">
                            Tổng số danh mục sản phẩm
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Dòng sản phẩm</CardTitle>
                        <FolderOpen className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{loading ? "-" : stats.productLines}</div>
                        <p className="text-xs text-muted-foreground">
                            Tổng số dòng sản phẩm
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Sản phẩm</CardTitle>
                        <Package className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{loading ? "-" : stats.products}</div>
                        <p className="text-xs text-muted-foreground">
                            Tổng số sản phẩm
                        </p>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="categories" className="space-y-4">
                <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="categories" className="flex items-center gap-2">
                        <Folder className="h-4 w-4" />
                        Danh mục
                    </TabsTrigger>
                    <TabsTrigger value="product-lines" className="flex items-center gap-2">
                        <FolderOpen className="h-4 w-4" />
                        Dòng sản phẩm
                    </TabsTrigger>
                    <TabsTrigger value="products" className="flex items-center gap-2">
                        <Package className="h-4 w-4" />
                        Sản phẩm
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="categories" className="space-y-4">
                    <CategoryManagement onDataChanged={fetchStats} />
                </TabsContent>

                <TabsContent value="product-lines" className="space-y-4">
                    <ProductLineManagement onDataChanged={fetchStats} />
                </TabsContent>

                <TabsContent value="products" className="space-y-4">
                    <ProductManagement onDataChanged={fetchStats} />
                </TabsContent>
            </Tabs>

            <Card className="mt-8">
                <CardHeader>
                    <CardTitle className="text-lg">Hướng dẫn sử dụng</CardTitle>
                    <CardDescription>
                        Quy trình tạo và quản lý cấu trúc sản phẩm
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="flex items-start gap-3">
                            <div className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">1</div>
                            <div>
                                <h4 className="font-medium">Tạo Danh mục</h4>
                                <p className="text-sm text-muted-foreground">
                                    Bắt đầu bằng cách tạo các danh mục chính (ví dụ: Critical Power, Thermal Management)
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="bg-green-100 text-green-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">2</div>
                            <div>
                                <h4 className="font-medium">Tạo Dòng sản phẩm</h4>
                                <p className="text-sm text-muted-foreground">
                                    Tạo các dòng sản phẩm thuộc danh mục (ví dụ: DC Power Systems, Room Cooling)
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="bg-orange-100 text-orange-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">3</div>
                            <div>
                                <h4 className="font-medium">Tạo Sản phẩm</h4>
                                <p className="text-sm text-muted-foreground">
                                    Tạo các sản phẩm cụ thể thuộc dòng sản phẩm (ví dụ: NetSure 801 Series)
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="bg-gray-100 text-gray-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">4</div>
                            <div>
                                <h4 className="font-medium">Upload Tài liệu</h4>
                                <p className="text-sm text-muted-foreground">
                                    Sử dụng trang Upload để thêm tài liệu vào các sản phẩm đã tạo
                                </p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
