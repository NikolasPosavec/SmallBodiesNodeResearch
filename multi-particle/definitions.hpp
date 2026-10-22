#ifndef DEFINITIONS_H
#define DEFINITIONS_H

// If problems with M_PI, comment these two lines and uncomment line 54.
#define _USE_MATH_DEFINES
#include <math.h>

#include <CGAL/Simple_cartesian.h>
#include <CGAL/AABB_tree.h>
#include <CGAL/AABB_traits.h>
#include <CGAL/AABB_triangle_primitive.h>
#include <CGAL/Vector_3.h>
#include <limits>
#include <CGAL/AABB_face_graph_triangle_primitive.h>
#include <CGAL/Polygon_mesh_processing/compute_normal.h>
#include <CGAL/Surface_mesh.h>
#include <CGAL/Polyhedron_3.h>
#include <string>
#include <optional>
#include <variant>
#include <boost/math/constants/constants.hpp>


enum HEADINGS : int {
    HEADING= 100,
    SUB_HEADING= 30
};

typedef CGAL::Simple_cartesian<double> K;
typedef K::FT FT;
typedef K::Ray_3 Ray;
typedef K::Line_3 Line;
typedef K::Point_3 Point;
typedef K::Triangle_3 Triangle;
typedef K::Vector_3 Vector3;
typedef std::list<Triangle>::iterator Iterator;



typedef CGAL::AABB_triangle_primitive<K, Iterator> Primitive;
typedef CGAL::AABB_traits<K, Primitive> Traits;
typedef CGAL::AABB_tree<Traits> Tree;

// CGAL 6 returns std::optional/std::variant (was boost::optional/boost::variant before CGAL 6)
typedef std::optional<Tree::Intersection_and_primitive_id<Ray>::Type> Ray_intersection;
typedef std::optional<Tree::Intersection_and_primitive_id<Line>::Type> Line_intersection;

typedef Tree::Primitive_id AABB_primitive_id;
typedef CGAL::Polyhedron_3<K> Polyhedron;


typedef Tree::Primitive_id PrimitiveType;

static double const MAXDBLVALUE = std::numeric_limits<double>::max();

// Pi from Boost
//const double M_PI = boost::math::constants::pi<double>();

struct MeshStats{
    double max_dist;
    double dX,dY,dZ;

    double area;

    MeshStats(std::vector<Point>& points){
        double maxs[3] = {-MAXDBLVALUE,-MAXDBLVALUE,-MAXDBLVALUE};
        std::vector<Point>::iterator it; 
        for(it = points.begin(); it != points.end(); it++)    {
            for(int i = 0;i<3;++i){
                if(std::abs((*it)[i])>maxs[i]) maxs[i] = std::abs((*it)[i]);
            }
        }
        max_dist = sqrt(maxs[0]*maxs[0]+maxs[1]*maxs[1]+maxs[2]*maxs[2]);
        dX = maxs[0];
        dY = maxs[1];
        dZ = maxs[2];
    }

    void compute_area(double radius){
        area = M_PI*std::pow(radius,2);
    }

};






inline std::string create_heading(char const * text, HEADINGS heading_size ){
    std::string str(text);
    return std::string("=")+str+std::string(heading_size-str.size(), '=');
}

inline std::string create_heading(std::string str, HEADINGS heading_size){
    return std::string("=")+str+std::string(heading_size-str.size(), '=');
}

inline void print_array(double* X, int n){
    for(int i=0;i<n;++i){
        std::cout << X[i] << " ";
    }
    std::cout << std::endl;
};


inline void multiply(double* F, double coeff, int n){
    for(int i=0;i<n;++i){
        F[i] = F[i]*coeff;
    }
};


static void centralize(std::vector<Point>& points){
    double mins[3] = {MAXDBLVALUE,MAXDBLVALUE,MAXDBLVALUE};
    double maxs[3] = {-MAXDBLVALUE,-MAXDBLVALUE,-MAXDBLVALUE};


    std::vector<Point>::iterator it; 

    for(it = points.begin(); it != points.end(); it++)    {
        for(int i = 0;i<3;++i){
            if((*it)[i]<mins[i]) mins[i] = (*it)[i];
            if((*it)[i]>maxs[i]) maxs[i] = (*it)[i];
        }
    }

    std::cout << "min values: " << mins[0] << "," << mins[1] << "," << mins[2] << std::endl;
    std::cout << "max values: " << maxs[0] << "," << maxs[1] << "," << maxs[2] << std::endl;

    Vector3 middle((mins[0]+maxs[0])*0.5,(mins[1]+maxs[1])*0.5,(mins[2]+maxs[2])*0.5);

    for(it = points.begin(); it != points.end(); it++)    {
        Point & point = *it;
        point = point-middle;
    }
}



#endif
